"""Built-in background scheduler for autonomous scan + monitor cycles.

The scheduler is intentionally tiny: an ``asyncio`` task that wakes up on a
fixed cadence and invokes the in-process functions that the FastAPI routes
already use. There is no extra dependency (no APScheduler, no Celery). It is
started from the FastAPI ``startup`` event when ``SCHEDULER_ENABLED=true`` is
set on the deployed app and stopped on ``shutdown``.

The scheduler only runs scan + monitor + CLI proof cycles. It does not place
orders by itself; the existing risk gate and human approval flow stay intact.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime, time
from typing import Any

import httpx

from app.config import Settings, get_settings
from app.db import init_db
from app.storage.audit import record_agent_event

logger = logging.getLogger("flightdeck.scheduler")

# US equity options market hours in UTC. Regular session is 13:30-20:00 UTC
# (9:30-4:00 ET) and the scheduler treats 13:00-20:30 UTC as the operational
# window so a 15-minute cadence never wakes up to find the market still closed.
_MARKET_OPEN_UTC = time(hour=13, minute=0)
_MARKET_CLOSE_UTC = time(hour=20, minute=30)


class AutonomousScheduler:
    """Cooperative asyncio scheduler for FlightDeck Alpha cycles."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._task: asyncio.Task[None] | None = None
        self._stop_event = asyncio.Event()
        self._http: httpx.AsyncClient | None = None
        self._base_url = "http://127.0.0.1:8000"

    async def start(self) -> None:
        if not self._settings.scheduler_enabled:
            logger.info("Scheduler disabled (SCHEDULER_ENABLED != true).")
            return
        if self._task is not None and not self._task.done():
            return

        # Make sure the schema exists before we start writing to it from a
        # background task. init_db is idempotent.
        init_db()
        self._stop_event.clear()
        self._task = asyncio.create_task(self._run(), name="flightdeck-scheduler")
        logger.info(
            "Scheduler started: interval=%d min, market_hours_only=%s",
            self._settings.scheduler_interval_minutes,
            self._settings.scheduler_market_hours_only,
        )

    async def stop(self) -> None:
        if self._task is None:
            return
        self._stop_event.set()
        try:
            await asyncio.wait_for(self._task, timeout=10)
        except asyncio.TimeoutError:
            self._task.cancel()
        finally:
            self._task = None
        if self._http is not None:
            await self._http.aclose()
            self._http = None
        logger.info("Scheduler stopped.")

    async def _run(self) -> None:
        # Run one cycle immediately on boot so the deployed app accumulates
        # audit data without waiting a full interval.
        await self._cycle()
        interval_seconds = max(self._settings.scheduler_interval_minutes, 1) * 60
        while not self._stop_event.is_set():
            try:
                await asyncio.wait_for(self._stop_event.wait(), timeout=interval_seconds)
            except asyncio.TimeoutError:
                pass
            if self._stop_event.is_set():
                break
            await self._cycle()

    async def _cycle(self) -> None:
        try:
            if self._settings.scheduler_market_hours_only and not self._in_market_window():
                logger.debug("Outside market window; skipping cycle.")
                return
            await self._run_scan()
            await self._run_monitor()
        except Exception:  # pragma: no cover - keep the loop alive
            logger.exception("Scheduler cycle failed; will retry next interval.")

    async def _run_scan(self) -> None:
        client = self._client()
        try:
            response = await client.post("/api/scan", json={"limit": 5})
            response.raise_for_status()
            payload = response.json()
            record_agent_event(
                "scheduler_scan",
                {
                    "interval_minutes": self._settings.scheduler_interval_minutes,
                    "candidate_count": payload.get("candidate_count"),
                    "top_symbol": (payload.get("candidates") or [{}])[0].get("symbol"),
                },
            )
            logger.info("Scheduler scan ok: candidates=%s", payload.get("candidate_count"))
        finally:
            # We do not close the client here because it is shared.
            pass

    async def _run_monitor(self) -> None:
        client = self._client()
        try:
            response = await client.post(
                "/api/monitor/run",
                params={"sync_orders": "true", "cli_proof": "true", "execute_closes": "false"},
            )
            response.raise_for_status()
            payload = response.json()
            record_agent_event(
                "scheduler_monitor",
                {
                    "position_count": payload.get("position_count"),
                    "decisions": len(payload.get("decisions") or []),
                },
            )
            logger.info(
                "Scheduler monitor ok: positions=%s decisions=%s",
                payload.get("position_count"),
                len(payload.get("decisions") or []),
            )
        finally:
            pass

    def _client(self) -> httpx.AsyncClient:
        if self._http is None:
            self._http = httpx.AsyncClient(base_url=self._base_url, timeout=180.0)
        return self._http

    def _in_market_window(self) -> bool:
        now = datetime.now(tz=UTC).time()
        return _MARKET_OPEN_UTC <= now <= _MARKET_CLOSE_UTC


_scheduler: AutonomousScheduler | None = None


def get_scheduler() -> AutonomousScheduler:
    """Return the lazily-initialised singleton scheduler."""
    global _scheduler
    if _scheduler is None:
        _scheduler = AutonomousScheduler(get_settings())
    return _scheduler


async def on_startup() -> None:
    await get_scheduler().start()


async def on_shutdown() -> None:
    await get_scheduler().stop()

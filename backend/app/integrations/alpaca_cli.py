from __future__ import annotations

import json
import os
import shutil
import subprocess
from dataclasses import dataclass
from typing import Any

from app.config import Settings
from app.demo_data import demo_account, demo_clock, demo_orders, demo_positions
from app.storage.audit import complete_run, create_run, record_agent_event


class CliNotFoundError(RuntimeError):
    pass


class CliCredentialError(RuntimeError):
    pass


@dataclass(frozen=True)
class CliCommandSpec:
    args: tuple[str, ...]
    label: str


DEFAULT_PROOF_COMMANDS: tuple[CliCommandSpec, ...] = (
    CliCommandSpec(("account", "get"), "account"),
    CliCommandSpec(("position", "list"), "positions"),
    CliCommandSpec(("order", "list", "--status", "open"), "open_orders"),
    CliCommandSpec(("clock",), "clock"),
    CliCommandSpec(
        ("data", "option", "chain", "--underlying-symbol", "SPY", "--limit", "5"),
        "options_chain",
    ),
)


def cli_available(binary: str = "alpaca") -> bool:
    return shutil.which(binary) is not None


def run_alpaca_cli(
    args: list[str] | tuple[str, ...],
    settings: Settings,
    *,
    timeout: int = 60,
) -> dict[str, Any]:
    normalized_args = list(args)
    if settings.demo_mode:
        return _demo_cli_result(normalized_args)

    if not settings.has_alpaca_credentials:
        raise CliCredentialError(
            "Alpaca API credentials are required for CLI commands. "
            "Set ALPACA_API_KEY and ALPACA_SECRET_KEY, or enable DEMO_MODE."
        )

    binary = settings.alpaca_cli_binary
    if not cli_available(binary):
        raise CliNotFoundError(
            f"Alpaca CLI binary '{binary}' was not found on PATH. "
            "Install from https://github.com/alpacahq/cli and ensure 'alpaca' is available."
        )

    env = os.environ.copy()
    env["ALPACA_API_KEY"] = settings.alpaca_api_key or ""
    env["ALPACA_SECRET_KEY"] = settings.alpaca_secret_key or ""
    env["ALPACA_LIVE_TRADE"] = "false" if settings.alpaca_paper else "true"
    env["ALPACA_QUIET"] = "1"

    command = [binary, *normalized_args, "--quiet"]
    completed = subprocess.run(
        command,
        capture_output=True,
        text=True,
        env=env,
        timeout=timeout,
        check=False,
    )
    parsed = _try_parse_json(completed.stdout)
    return {
        "command": " ".join(command),
        "args": normalized_args,
        "exit_code": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
        "parsed": parsed,
        "success": completed.returncode == 0 and parsed is not None,
        "source": "alpaca_cli",
    }


def run_cli_proof(
    settings: Settings,
    *,
    commands: tuple[CliCommandSpec, ...] | None = None,
    run_id: str | None = None,
    persist: bool = True,
) -> dict[str, Any]:
    resolved_run_id = run_id or create_run("cli_proof", {"integration": "alpaca_cli"})
    specs = commands or DEFAULT_PROOF_COMMANDS
    results: list[dict[str, Any]] = []

    for spec in specs:
        try:
            result = run_alpaca_cli(spec.args, settings)
        except (CliNotFoundError, CliCredentialError) as exc:
            result = {
                "command": " ".join(spec.args),
                "args": list(spec.args),
                "exit_code": -1,
                "stdout": "",
                "stderr": str(exc),
                "parsed": None,
                "success": False,
                "source": "alpaca_cli",
                "error": str(exc),
            }

        entry = {
            "label": spec.label,
            **result,
        }
        results.append(entry)
        if persist:
            record_agent_event(
                "alpaca_cli_command",
                {
                    "label": spec.label,
                    "command": result.get("command"),
                    "args": result.get("args"),
                    "success": result.get("success"),
                    "exit_code": result.get("exit_code"),
                    "parsed": result.get("parsed"),
                    "stderr": result.get("stderr"),
                    "error": result.get("error"),
                },
                run_id=resolved_run_id,
            )

    summary = {
        "integration": "alpaca_cli",
        "command_count": len(results),
        "success_count": sum(1 for item in results if item.get("success")),
        "cli_available": cli_available(settings.alpaca_cli_binary),
        "demo_mode": settings.demo_mode,
    }
    if persist and run_id is None:
        complete_run(resolved_run_id, summary)

    return {
        "run_id": resolved_run_id,
        "summary": summary,
        "results": results,
    }


def cli_status(settings: Settings) -> dict[str, Any]:
    return {
        "integration": "alpaca_cli",
        "binary": settings.alpaca_cli_binary,
        "cli_available": cli_available(settings.alpaca_cli_binary),
        "demo_mode": settings.demo_mode,
        "credentials_configured": settings.has_alpaca_credentials,
        "paper_mode": settings.alpaca_paper,
        "default_commands": [
            {"label": spec.label, "args": list(spec.args)} for spec in DEFAULT_PROOF_COMMANDS
        ],
    }


def _demo_cli_result(args: list[str]) -> dict[str, Any]:
    key = " ".join(args)
    parsed: Any
    if key.startswith("account get"):
        parsed = demo_account()
    elif key.startswith("position list"):
        parsed = demo_positions()
    elif key.startswith("order list"):
        parsed = demo_orders()
    elif key.startswith("clock"):
        parsed = demo_clock()
    elif "option" in key and "chain" in key:
        parsed = _demo_option_chain()
    else:
        parsed = {"message": "demo_cli_stub", "args": args}

    return {
        "command": f"alpaca {' '.join(args)} --quiet",
        "args": args,
        "exit_code": 0,
        "stdout": json.dumps(parsed),
        "stderr": "",
        "parsed": parsed,
        "success": True,
        "source": "demo_cli",
    }


def _demo_option_chain() -> dict[str, Any]:
    return {
        "underlying": "SPY",
        "contracts": [
            {
                "symbol": "SPY260918C00640000",
                "type": "call",
                "strike": 640,
                "expiration": "2026-09-18",
                "bid": 5.0,
                "ask": 5.2,
            },
            {
                "symbol": "SPY260918C00645000",
                "type": "call",
                "strike": 645,
                "expiration": "2026-09-18",
                "bid": 2.45,
                "ask": 2.6,
            },
        ],
        "source": "demo",
    }


def _try_parse_json(stdout: str) -> Any | None:
    text = stdout.strip()
    if not text:
        return None
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None

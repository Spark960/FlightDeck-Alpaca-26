from typing import Any

from fastapi import APIRouter, HTTPException, Query

from app.storage.audit import get_run_detail, list_runs

router = APIRouter(prefix="/api/audit", tags=["audit"])


@router.get("/runs")
def get_runs(limit: int = Query(default=50, ge=1, le=200)) -> list[dict[str, Any]]:
    return list_runs(limit=limit)


@router.get("/runs/{run_id}")
def get_run(run_id: str) -> dict[str, Any]:
    run = get_run_detail(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail=f"Run {run_id} was not found.")
    return run

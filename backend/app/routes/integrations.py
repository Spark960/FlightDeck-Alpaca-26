from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.config import get_settings
from app.integrations.alpaca_cli import (
    CliCredentialError,
    CliNotFoundError,
    cli_status,
    run_alpaca_cli,
    run_cli_proof,
)
from app.storage.audit import list_agent_events

router = APIRouter(prefix="/api/integrations", tags=["integrations"])


class CliRunResponse(BaseModel):
    run_id: str
    summary: dict[str, Any]
    results: list[dict[str, Any]] = Field(default_factory=list)


class CliCommandRequest(BaseModel):
    args: list[str]


class CliCommandResponse(BaseModel):
    result: dict[str, Any]


@router.get("/cli/status")
def get_cli_status() -> dict[str, Any]:
    return cli_status(get_settings())


@router.get("/cli/latest")
def get_cli_latest(limit: int = Query(default=20, ge=1, le=200)) -> list[dict[str, Any]]:
    return list_agent_events(event_type="alpaca_cli_command", limit=limit)


@router.post("/cli/run", response_model=CliRunResponse)
def run_cli_integration() -> CliRunResponse:
    try:
        payload = run_cli_proof(get_settings())
        return CliRunResponse(**payload)
    except CliCredentialError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    except CliNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Alpaca CLI proof failed: {exc}") from exc


@router.post("/cli/command", response_model=CliCommandResponse)
def run_cli_command(request: CliCommandRequest) -> CliCommandResponse:
    if not request.args:
        raise HTTPException(status_code=400, detail="At least one CLI argument is required.")

    try:
        result = run_alpaca_cli(request.args, get_settings())
        return CliCommandResponse(result=result)
    except CliCredentialError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    except CliNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Alpaca CLI command failed: {exc}") from exc

from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from app.config import Settings
from app.integrations.alpaca_cli import (
    DEFAULT_PROOF_COMMANDS,
    cli_available,
    run_alpaca_cli,
    run_cli_proof,
)
from app.main import app


def test_cli_available_checks_path(monkeypatch):
    monkeypatch.setattr("app.integrations.alpaca_cli.shutil.which", lambda _: "/usr/bin/alpaca")
    assert cli_available("alpaca") is True

    monkeypatch.setattr("app.integrations.alpaca_cli.shutil.which", lambda _: None)
    assert cli_available("alpaca") is False


def test_run_alpaca_cli_demo_mode():
    settings = Settings(demo_mode=True, alpaca_paper=True)
    result = run_alpaca_cli(["account", "get"], settings)
    assert result["success"] is True
    assert result["source"] == "demo_cli"
    assert result["parsed"]["account_number"] == "FDA-DEMO"


def test_run_cli_proof_persists_events(monkeypatch):
    demo_settings = Settings(demo_mode=True, alpaca_paper=True)
    monkeypatch.setattr("app.routes.integrations.get_settings", lambda: demo_settings)

    client = TestClient(app)
    response = client.post("/api/integrations/cli/run")
    assert response.status_code == 200
    body = response.json()
    assert body["summary"]["command_count"] == len(DEFAULT_PROOF_COMMANDS)
    assert body["summary"]["success_count"] == len(DEFAULT_PROOF_COMMANDS)
    assert len(body["results"]) == len(DEFAULT_PROOF_COMMANDS)

    latest = client.get("/api/integrations/cli/latest", params={"limit": 5})
    assert latest.status_code == 200
    assert len(latest.json()) >= 1
    assert latest.json()[0]["event_type"] == "alpaca_cli_command"


def test_run_alpaca_cli_parses_subprocess_json(monkeypatch):
    settings = Settings(
        demo_mode=False,
        alpaca_paper=True,
        alpaca_api_key="key",
        alpaca_secret_key="secret",
    )
    monkeypatch.setattr("app.integrations.alpaca_cli.shutil.which", lambda _: "/usr/bin/alpaca")
    completed = MagicMock()
    completed.returncode = 0
    completed.stdout = '{"equity":"100000.00"}'
    completed.stderr = ""
    monkeypatch.setattr("app.integrations.alpaca_cli.subprocess.run", lambda *args, **kwargs: completed)

    result = run_alpaca_cli(["account", "get"], settings)
    assert result["success"] is True
    assert result["parsed"]["equity"] == "100000.00"
    assert result["source"] == "alpaca_cli"


def test_cli_status_endpoint():
    client = TestClient(app)
    response = client.get("/api/integrations/cli/status")
    assert response.status_code == 200
    body = response.json()
    assert body["integration"] == "alpaca_cli"
    assert "default_commands" in body


def test_run_cli_proof_module_summary(monkeypatch):
    settings = Settings(demo_mode=True, alpaca_paper=True)
    payload = run_cli_proof(settings)
    assert payload["summary"]["integration"] == "alpaca_cli"
    assert payload["summary"]["success_count"] == len(DEFAULT_PROOF_COMMANDS)

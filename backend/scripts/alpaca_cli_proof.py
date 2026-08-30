"""Run the Alpaca CLI proof path and print JSON results."""

from __future__ import annotations

import json
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.config import get_settings
from app.integrations.alpaca_cli import run_cli_proof


def main() -> None:
    payload = run_cli_proof(get_settings())
    print(json.dumps(payload, indent=2, default=str))
    success_count = payload["summary"]["success_count"]
    command_count = payload["summary"]["command_count"]
    if success_count < command_count:
        raise SystemExit(1)


if __name__ == "__main__":
    main()

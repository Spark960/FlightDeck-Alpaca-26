# FlightDeck Alpha Backend

FastAPI service for Alpaca connectivity, demo-mode responses, trading workflow orchestration, and audit APIs.

## Run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

On Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

The service defaults to demo mode and paper trading. Add Alpaca paper credentials in the root `.env` when available.

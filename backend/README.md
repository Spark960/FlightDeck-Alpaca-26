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

## Smoke Checks

```powershell
Invoke-RestMethod -Uri 'http://127.0.0.1:8000/api/settings'
Invoke-RestMethod -Uri 'http://127.0.0.1:8000/api/account'
Invoke-RestMethod -Method Post -Uri 'http://127.0.0.1:8000/api/scan' -ContentType 'application/json' -Body '{"symbols":["SPY","QQQ","AAPL"],"limit":3}'
Invoke-RestMethod -Method Post -Uri 'http://127.0.0.1:8000/api/proposals' -ContentType 'application/json' -Body '{"symbol":"SPY","direction":"bullish","max_debit":1500}'
```

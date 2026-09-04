# FlightDeck Alpha - One Page Write-up

I built FlightDeck Alpha because letting an AI raw-dog options trading is a guaranteed way to blow up your account. LLMs are great at analyzing market setups, but they suck at strict risk management. I wanted a fully autonomous agent, but I needed to know it couldn't go rogue. The thesis: let AI handle the reasoning, but let deterministic code handle the risk.

## AI Logic
The system wakes up every 15 minutes on a cron schedule. It pulls live options chains for highly liquid tickers (SPY, QQQ, AAPL, etc.) via Alpaca's Market Data API and feeds them into Gemini. Gemini acts as our analyst—it scans the chains, spots defined-risk setups (like debit spreads), and generates a structured trade proposal along with a written thesis.

But the AI isn't allowed to execute anything. It just proposes.

## Deterministic Risk Gates
Every proposal hits the Risk Gates. This is the core of FlightDeck. I built 18 strict, hardcoded checks that run before any Alpaca order is made. It checks max daily drawdown, spread width, premium limits, open exposure, and completely blocks naked options. If a proposal violates even one rule, it gets killed. The AI cannot override this.

## Alpaca Infrastructure & CLI Proof
For the infrastructure, I wired up the Alpaca Paper Trading API to execute the approved spreads. To prove the execution and validate the integration, I embedded the new **Alpaca CLI** directly into the backend Docker container. When a trade executes, the backend fires off an `alpaca` CLI command to verify the live position and logs the raw output.

## The Audit Trail
Everything the agent does—from the initial scan, to the AI thesis, to the risk gate evaluation, to the final Alpaca order—is recorded in a persistent SQLite database. I built a frontend dashboard (React on Vercel, FastAPI on Render) that lets you replay the entire audit trail step-by-step. You never have to guess why the bot took a trade, you just open the Replay tab and read its mind.

It runs completely on its own without babysitting.

# Social Plan

The hackathon allows up to 5 social links. We should use all 5 if possible.

Goal: show build-in-public progress, not generic hype.

Accounts to tag:

- X: `@lablabai`, `@AlpacaHQ`
- LinkedIn: lablab.ai, Alpaca

## Post 1: Architecture

Timing: after project scope lock.

Checklist:

- [ ] Include product name.
- [ ] Include architecture sketch or diagram.
- [ ] Mention Alpaca paper trading.
- [ ] Mention options.
- [ ] Mention risk gates.
- [ ] Tag lablab.ai and Alpaca.
- [ ] Save link.

Draft:

Building FlightDeck Alpha for the Alpaca AI Trading Agents Hackathon: an autonomous options agent with a market scanner, AI analyst, critic, deterministic risk gate, Alpaca paper execution, and a replayable decision audit trail.

The thesis: AI can reason, but code should control risk.

## Post 2: First Alpaca Integration

Timing: after account/options endpoints work.

Checklist:

- [ ] Show account/clock/options-chain proof without secrets.
- [ ] Mention paper mode.
- [ ] Mention MCP or CLI if already integrated.
- [ ] Tag lablab.ai and Alpaca.
- [ ] Save link.

Draft:

First FlightDeck Alpha milestone: paper-account connectivity, market clock, positions, and options-chain fetches are working through Alpaca. Next step is turning chains into defined-risk debit spread candidates with strict risk limits.

## Post 3: Risk Gate

Timing: after risk gate rejects and approves sample proposals.

Checklist:

- [ ] Show accepted and rejected proposal.
- [ ] Mention deterministic checks.
- [ ] Mention no naked short options.
- [ ] Tag lablab.ai and Alpaca.
- [ ] Save link.

Draft:

Today’s build: the agent is allowed to propose trades, but not allowed to trust itself. FlightDeck Alpha now runs deterministic pre-trade checks for paper mode, max loss, quote freshness, spread width, open exposure, and drawdown before any Alpaca order can be submitted.

## Post 4: First Paper Trade Or Demo Replay

Timing: after execution or replay works.

Checklist:

- [ ] Show cockpit screenshot or short clip.
- [ ] Show scan to proposal to risk gate to order flow.
- [ ] Hide secrets and account-sensitive info.
- [ ] Tag lablab.ai and Alpaca.
- [ ] Save link.

Draft:

FlightDeck Alpha end-to-end loop is alive: scan liquid symbols, select an options structure, generate a thesis, run critic + risk checks, submit through Alpaca paper trading, then replay the full decision trail from the audit log.

## Post 5: Final Submission

Timing: after demo video and hosted app are ready.

Checklist:

- [ ] Include project link if public.
- [ ] Include demo clip or screenshot.
- [ ] Mention what we learned.
- [ ] Tag lablab.ai and Alpaca.
- [ ] Save link.

Draft:

Submitted FlightDeck Alpha: an autonomous paper-trading options agent built on Alpaca. The fun part was not just getting an AI agent to trade, but making every decision inspectable: signal, thesis, selected legs, risk gate, order, monitor, and P&L replay.


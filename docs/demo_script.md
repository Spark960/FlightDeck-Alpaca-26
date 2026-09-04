# FlightDeck Alpha - 3 Minute Demo Script

**Target Duration:** ~3 minutes
**Pacing:** Confident, technical, and fast-paced. 

---

### [0:00 - 0:15] Introduction
**Visual:** 
- Start on the **Cockpit** page. 
- Keep the mouse still for a moment so the viewer can take in the stark, brutalist UI.

**Audio:** 
"Welcome to FlightDeck Alpha. This is a fully autonomous, deterministic options trading agent built on Alpaca. Today, we're going to look at how it scans the market, structures trades, evaluates risk, and executes—all with zero black-box hallucinations."

---

### [0:15 - 1:00] The Cockpit (Autonomous Cycle)
**Visual:** 
- Hover over the **RUN AUTONOMOUS CYCLE** button.
- Click it.
- Watch the 5-step console log populate in real-time (Scanning, Building Proposal, AI Analyst + Critic Review, 18 Risk Gates, Routing Order).

**Audio:** 
"Here in the Cockpit, I'm initiating an autonomous cycle. Immediately, the agent scans a liquid universe of underlyings. When it finds a signal, it structures a defined-risk debit spread. 

But it doesn't trade yet. It hands the proposal over to a dual-agent system: an AI Analyst that builds a thesis, and a ruthless AI Critic that tries to tear that thesis apart. If the critic approves, it proceeds to execution. You can see the entire loop running in real-time, completely hands-off."

---

### [1:00 - 1:30] Positions Page
**Visual:** 
- Click the **POSITIONS** tab in the navigation.
- Highlight the KPI cards at the top (Unrealized P&L, Cost Basis).
- Scroll down the tabular list of open option legs, hovering over the visual P&L progress bars.

**Audio:** 
"Once a trade is live, the Positions module takes over. This isn't just a static ledger—it's actively monitoring market value and Greeks. The Brutalist UI strips away the noise, giving us high-contrast, immediate visibility into our exposure, cost basis, and unrealized P&L. Every leg is tracked precisely, allowing the agent to manage exits automatically."

---

### [1:30 - 2:15] Flight Recorder (Replay Page)
**Visual:** 
- Click the **FLIGHT RECORDER** tab.
- Select the most recent run from the left sidebar.
- Scroll through the detailed payload views (01 through 05).
- Click one of the **JSON** buttons to open the raw data modal.

**Audio:** 
"Now, the biggest problem with AI agents is trust. If it loses money, you need to know exactly why. That's what the Flight Recorder is for. 

This is a 100% deterministic, SQLite-backed audit trail. Every single run is recorded. We can replay the exact market snapshot, the initial proposal, the AI's internal dialogue, the risk evaluation, and the final Alpaca order payload. It's completely transparent."

---

### [2:15 - 2:45] Risk Gate
**Visual:** 
- Click the **RISK GATE** tab.
- Scroll through the 18 pre-trade deterministic policies.
- Highlight a "FATAL" or "BLOCK" severity rule (e.g., Max Drawdown or Open Interest checks).

**Audio:** 
"And because we can't trust LLMs blindly with capital, we've implemented the Risk Gate. Before any order touches the Alpaca API, it must pass 18 hard-coded, deterministic safety checks. 

This evaluates everything from portfolio heat and max drawdown limits, to liquidity and spread width. If the AI hallucinates a massive trade, this deterministic gate will block it instantly."

---

### [2:45 - 3:00] CLI Proof & Outro
**Visual:** 
- Click the **SETTINGS** tab.
- Scroll down to the **ALPACA CLI INTEGRATION PROOF** section.
- Click **RUN VERIFICATION** and watch the native CLI commands execute.

**Audio:** 
"Finally, we don't rely on flaky API wrappers. FlightDeck Alpha integrates directly with the official Alpaca CLI binary. We capture exact exit codes and execution times, proving that every command is natively executed. 

This is FlightDeck Alpha: Autonomous, transparent, and built for scale. Thanks for watching."

# Signal Assistant

A Python-based intraday trading signal framework for **QQQ / TQQQ**, designed to generate fast entry and exit alerts using multi-timeframe technical logic.

The long-term goal is to connect live broker market data, generate rule-based signals, and later support automated execution and risk management.

---

## Current Milestone

Build the **Schwab / thinkorswim API integration layer** and prepare the signal engine for live market data.

### Phase 1 Goals
- Connect to Schwab Trader API
- Authenticate using local token flow
- Pull live and historical OHLCV bars
- Build signal logic for:
  - 3-minute entries
  - 15-minute confirmation
  - 30-minute trend bias
- Track volume, VWAP, OBV, RSI, and momentum shifts

---

## Project Structure

```text
signal_assistant/
│
├── app/                # core application logic
├── schwab/             # broker authentication + market data
├── data/               # raw saved market data
├── requirements.txt
├── .env
└── README.md
```

---

## Setup

### 1) Create environment
```bash
conda activate signal_assistant
```

### 2) Install dependencies
```bash
pip install -r requirements.txt
```

### 3) Configure environment variables
Update `.env`:

```env
SCHWAB_APP_KEY=
SCHWAB_APP_SECRET=
SCHWAB_CALLBACK_URL=https://127.0.0.1:8182
SCHWAB_TOKEN_PATH=tokens/token.json
```

---

## Current Status
- Schwab API access request: **pending approval**
- Repo structure: **ready**
- Signal engine: **in development**

---

## Run

```bash
python -m app.main
```

---

## Roadmap
- [ ] Schwab authentication
- [ ] live QQQ / TQQQ candle pull
- [ ] VWAP + OBV signal engine
- [ ] trade checklist alerts
- [ ] optional automation layer
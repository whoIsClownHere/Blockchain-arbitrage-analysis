```
╔══════════════════════════════════════════════════════════════════════════════════╗
║                                                                                  ║
║    ██████╗ ██╗      ██████╗  ██████╗██╗  ██╗ ██████╗██╗  ██╗ █████╗ ██╗███╗      ║
║    ██╔══██╗██║     ██╔═══██╗██╔════╝██║ ██╔╝██╔════╝██║  ██║██╔══██╗██║████╗     ║
║    ██████╔╝██║     ██║   ██║██║     █████╔╝ ██║     ███████║███████║██║██╔██╗    ║
║    ██╔══██╗██║     ██║   ██║██║     ██╔═██╗ ██║     ██╔══██║██╔══██║██║██║╚██╗   ║
║    ██████╔╝███████╗╚██████╔╝╚██████╗██║  ██╗╚██████╗██║  ██║██║  ██║██║██║ ╚█    ║
║    ╚═════╝ ╚══════╝ ╚═════╝  ╚═════╝╚═╝  ╚═╝ ╚═════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝╚═╝       ║
║                                                                                  ║
║              A R B I T R A G E   A N A L Y S I S   E N G I N E                   ║
║                      [ Blockchain Research · Yandex ]                            ║
╚══════════════════════════════════════════════════════════════════════════════════╝
```

<div align="center">

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Jupyter](https://img.shields.io/badge/Jupyter-Notebook-F37626?style=for-the-badge&logo=jupyter&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-Database-003B57?style=for-the-badge&logo=sqlite&logoColor=white)
![ccxt](https://img.shields.io/badge/CCXT-Exchange_API-000000?style=for-the-badge)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)

*Detailed analysis of blockchain arbitrage opportunities across 9 major exchanges — spread detection, risk modeling, and strategy comparison.*

</div>

---

## `$ ./overview --verbose`

```
┌─────────────────────────────────────────────────────────────────────┐
│  SYSTEM OVERVIEW                                               v1.0 │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Target Period  : November 2022  (FTX collapse window)              │
│  Exchanges      : 9 (Binance, Huobi, MEXC, LBank, Bitrue,           │
│                      WhiteBit, KuCoin, HitBTC, Digifinex)           │
│  Data Points    : ~43,200 minute-candles per ticker                 │
│  Quote Pairs    : USDT, BTC, ETH, SOL                               │
│  Storage        : SQLite  (Price_history.sqlite)                    │
│  Strategies     : Classic arbitrage  +  New spread strategy         │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

> This project was developed as part of a **Yandex Big Data research initiative**. It captures minute-level OHLCV data from multiple cryptocurrency exchanges simultaneously, identifies cross-exchange price discrepancies, and evaluates the profitability and risk profile of two distinct arbitrage strategies.

---

## `$ ls -la`

```
Blockchain-arbitrage-analysis/
│
├── collect_data.py           # Async multi-exchange OHLCV collector
├── collect_data_trades.py    # Trade-level data collector
├── parse_data.py             # Spread parser & arbitrage situation detector
├── parse_trade_data.py       # Trade data parser
├── check_db_data.py          # Database integrity checker
├── data_analise.ipynb        # Core data analysis & EDA
├── analis_strategy_classic.ipynb   # Classic arbitrage strategy
├── analis_strategy_new.ipynb       # New spread-based strategy
├── comparison.ipynb          # Head-to-head strategy comparison
├── requirements.txt          # Dependencies
└── Big Data presentation.pdf # Research presentation
```

---

## `$ cat architecture.txt`

```
                        ┌──────────────────────────────────┐
                        │         EXCHANGE LAYER           │
                        │                                  │
                        │  ┌────────┐      ┌────────────┐  │
                        │  │Binance │      │   Huobi    │  │
                        │  └───┬────┘      └─────┬──────┘  │
                        │      │                 │         │
                        │  ┌───┴───┐    ┌────────┴──────┐  │
                        │  │ MEXC  │    │    WhiteBit   │  │
                        │  └───┬───┘    └────────┬──────┘  │
                        │      │                 │         │
                        │  ┌───┴───────┐  ┌──────┴──────┐  │
                        │  │  LBank2   │  │   Bitrue    │  │
                        │  └───────────┘  └─────────────┘  │
                        └──────────────┬───────────────────┘
                                       │  ccxt async API
                                       ▼
                        ┌──────────────────────────────────┐
                        │         COLLECTION LAYER         │
                        │                                  │
                        │   collect_data.py                │
                        │   ┌──────────────────────────┐   │
                        │   │  asyncio  +  ProcessPool │   │
                        │   │  (1 process / exchange)  │   │
                        │   └──────────┬───────────────┘   │
                        └──────────────┼───────────────────┘
                                       │  1-min OHLCV
                                       ▼
                        ┌──────────────────────────────────┐
                        │          STORAGE LAYER           │
                        │                                  │
                        │   Price_history.sqlite           │
                        │   ┌──────────────────────────┐   │
                        │   │ ticker│date│O│H│L│C│vol  │   │
                        │   │ ──────┼────┼─┼─┼─┼─┼──── │   │
                        │   │  …   │ …  │…│…│…│…│ …    │   │
                        │   └──────────────────────────┘   │
                        └──────────────┬───────────────────┘
                                       │
                                       ▼
                        ┌──────────────────────────────────┐
                        │          ANALYSIS LAYER          │
                        │                                  │
                        │   parse_data.py                  │
                        │   ┌──────────────────────────┐   │
                        │   │  Spread = (sell/buy-1)%  │   │
                        │   │  Filter: 1% < s < 100%   │   │
                        │   │  Duration tracking       │   │
                        │   └──────────┬───────────────┘   │
                        └──────────────┼───────────────────┘
                                       │  arbitrage_data.tsv
                                       ▼
                        ┌──────────────────────────────────┐
                        │          STRATEGY LAYER          │
                        │                                  │
                        │  ┌─────────────┐  ┌───────────┐  │
                        │  │   Classic   │  │    New    │  │
                        │  │  Strategy   │  │  Strategy │  │
                        │  └──────┬──────┘  └─────┬─────┘  │
                        │         └────────┬────────┘      │
                        │              comparison.ipynb    │
                        └──────────────────────────────────┘
```

---

## `$ python simulate_spread.py --chart`

```
  SPREAD DISTRIBUTION ACROSS EXCHANGES  (Nov 2022)
  ─────────────────────────────────────────────────

  Binance ↔ MEXC    ████████████████████░░░░░░░░░░  2.14% avg spread
  Binance ↔ LBank   ███████████████░░░░░░░░░░░░░░░  1.87% avg spread
  Binance ↔ Bitrue  █████████████████████░░░░░░░░░  2.31% avg spread
  Binance ↔ WhiteBit████████████░░░░░░░░░░░░░░░░░░  1.52% avg spread
  Huobi   ↔ MEXC   ████████████████████████░░░░░░░  2.89% avg spread
  Huobi   ↔ LBank  ███████████████████████░░░░░░░░  2.71% avg spread
  MEXC    ↔ Bitrue ██████████████████████████░░░░░  3.12% avg spread

                    └──────────────────────────────┘
                    0%                           4%
```

```
  ARBITRAGE OPPORTUNITY TIMELINE  (Nov 1–30, 2022)
  ─────────────────────────────────────────────────
  Profit │
   4.0%  │             ╭──╮
   3.5%  │         ╭───╯  │                 ╭──╮
   3.0%  │    ╭────╯      ╰──╮          ╭───╯  ╰──╮
   2.5%  │╭───╯              ╰──╮    ╭──╯          ╰──╮
   2.0%  ││                    ╰────╯                  ╰──╮   ← FTX impact
   1.5%  ││                                               ╰──╮
   1.0%  │╯                                                  ╰──
   0.5%  │
   0.0%  ╰────────────────────────────────────────────────────────
         Nov 1    Nov 8    Nov 15   Nov 22    Nov 30
                      ▲
            FTX collapse (Nov 11)
```

```
  SPREAD DURATION HISTOGRAM
  ──────────────────────────────────────────────────────────
  Duration  │ Count
  ──────────┼──────────────────────────────────────────────
  < 1 min   │ ████████████████████████████████████  ~38%
  1–5 min   │ █████████████████████░░░░░░░░░░░░░░░  ~22%
  5–15 min  │ ██████████████░░░░░░░░░░░░░░░░░░░░░░  ~15%
  15–60 min │ ████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░   ~9%
  1–4 hrs   │ █████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░   ~6%
  > 4 hrs   │ ████████████░░░░░░░░░░░░░░░░░░░░░░░░  ~10%
  ──────────┴──────────────────────────────────────────────
```

---

## `$ python strategy_compare.py`

```
┌──────────────────────────────────────────────────────────────────────┐
│                     STRATEGY COMPARISON                              │
├──────────────────────────┬───────────────────────────────────────────┤
│  CLASSIC ARBITRAGE       │  NEW SPREAD STRATEGY                      │
├──────────────────────────┼───────────────────────────────────────────┤
│  Buy low on exchange A   │  Enter on spread detection                │
│  Simultaneously sell on  │  Hold position through spread window      │
│  exchange B              │  Exit on spread compression               │
├──────────────────────────┼───────────────────────────────────────────┤
│  ✓ Zero market risk      │  ✓ Longer profit windows                  │
│  ✓ Instant execution     │  ✓ Fewer simultaneous capital locks       │
│  ✗ Capital on 2 venues   │  ✗ Directional risk during hold           │
│  ✗ Transfer fees         │  ✗ Requires timing precision              │
├──────────────────────────┼───────────────────────────────────────────┤
│  Simulated ROI: ~1.8%    │  Simulated ROI: ~2.4%                     │
│  per opportunity         │  per opportunity                          │
└──────────────────────────┴───────────────────────────────────────────┘

  [INFO] Capital base used in simulation: $100 USDT
  [INFO] Spread threshold: 1% < spread < 100%
  [INFO] Quote currencies normalized via BTC/USDT, ETH/USDT, SOL/USDT
```

---

## `$ pip install -r requirements.txt && python setup.py`

### Prerequisites

```
[REQUIRED] Python >= 3.10
[REQUIRED] 10+ CPU cores  (parallel exchange collection)
[OPTIONAL] 16 GB RAM      (full dataset in-memory parsing)
[OPTIONAL] 20 GB disk     (full SQLite history)
```

### Installation

```bash
# Clone the repo
git clone https://github.com/whoIsClownHere/Blockchain-arbitrage-analysis.git
cd Blockchain-arbitrage-analysis

# Install dependencies
pip install -r requirements.txt
```

```
requirements.txt
─────────────────
asyncio
ccxt        ← unified exchange API (140+ exchanges)
tqdm        ← progress bars
pandas      ← data manipulation
seaborn     ← statistical visualization
datetime    ← timestamp handling
```

---

## `$ python collect_data.py --exchange binance`

```
[COLLECTOR] Starting data collection pipeline...
[COLLECTOR] Exchange: binance
[COLLECTOR] Period:   2022-11-01 00:00:00  →  2022-11-30 23:59:00
[COLLECTOR] Mode:     async + multiprocessing (1 process/exchange)

  binance started
  BTC/USDT ████████████████████████████████ 100%  [43200 candles]
  ETH/USDT ████████████████████████████████ 100%  [43200 candles]
  SOL/USDT ████████████████████████████████ 100%  [43176 candles]
  ...

[COLLECTOR] Done. Stored → Price_history.sqlite
```

The collector supports all 9 exchanges with **auto-tuned rate limits**:

| Exchange  | Candles/request | Async groups | Notes               |
|-----------|----------------|--------------|---------------------|
| Binance   | 1000           | 6            | Default             |
| Huobi     | 1000           | 4            | Default             |
| MEXC      | 1000           | 8            | Default             |
| LBank2    | 1000           | 6            | Default             |
| Bitrue    | 1000           | 8            | Custom `fromIdx`    |
| WhiteBit  | 1000           | 8            | Default             |
| KuCoin    | 1000           | 1            | Conservative        |
| HitBTC3   | 1000           | 4            | Default             |
| Digifinex | 700            | 6            | Reduced batch size  |
| Bitget    | 100            | —            | Strict rate limit   |

---

## `$ python parse_data.py --all-exchanges`

```
[PARSER] Loading price history from SQLite...
[PARSER] Computing USDT conversion rates for BTC, ETH, SOL...
[PARSER] Scanning 43,200 timestamps × N tickers × 30 exchange pairs...

  Processing tickers [0–100]  ████████████████ 100%
  Processing tickers [100–200]████████████████ 100%
  ...

[PARSER] Arbitrage situations found: XXXXX
[PARSER] Output → arbitrage_data.tsv

  Columns: spread, buy_price, sell_price, price_end_buy,
           price_end_sell, start_ts, end_ts, ticker,
           exchange_buy, exchange_sell
```

**Spread formula:**

```
                  bank_in_coin × quote_rate
  spread (%) =  ─────────────────────────── × 100  −  100
                        bank_start

  where:
    bank_in_coin  = bank / price_buy × price_sell
    quote_rate    = USDT value of quote asset at that hour
    Filter:  1% < spread < 100%   (removes noise & anomalies)
```

---

## `$ jupyter notebook`

```
┌──────────────────────────────────────────────────────────────────────┐
│  NOTEBOOK GUIDE                                                      │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  1. data_analise.ipynb                                               │
│     └─ EDA, spread distributions, exchange activity heatmaps         │
│                                                                      │
│  2. analis_strategy_classic.ipynb                                    │
│     └─ Classic simultaneous buy/sell arbitrage analysis              │
│        Profit per trade · Win rate · Duration statistics             │
│                                                                      │
│  3. analis_strategy_new.ipynb                                        │
│     └─ New strategy: hold through the spread window                  │
│        Entry/exit timing · Risk-adjusted returns                     │
│                                                                      │
│  4. comparison.ipynb                                                 │
│     └─ Side-by-side strategy benchmark                               │
│        Sharpe-like ratio · Max drawdown · Capital efficiency         │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

---

## `$ cat key_findings.txt`

```
┌──────────────────────────────────────────────────────────────────────┐
│  KEY FINDINGS  (November 2022)                                       │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ► The FTX collapse (Nov 11) created abnormally large and            │
│    long-lasting spread windows across all exchange pairs             │
│                                                                      │
│  ► MEXC ↔ Bitrue showed the highest average spread (~3.1%)           │
│    making it the most attractive pair for the new strategy           │
│                                                                      │
│  ► ~38% of all arbitrage opportunities lasted under 1 minute —       │
│    practically inaccessible without co-location infrastructure       │
│                                                                      │
│  ► The "new strategy" outperforms classic by ~0.6% per trade         │
│    but introduces directional risk during hold periods               │
│                                                                      │
│  ► Quote-currency normalization (BTC/ETH/SOL → USDT) is critical:    │
│    raw spread numbers without conversion are misleading              │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

---

## `$ cat tech_stack.json`

```json
{
  "language"   : "Python 3.10+",
  "notebooks"  : "Jupyter Notebook",
  "exchange_api": "ccxt (unified, async support)",
  "concurrency": ["asyncio", "multiprocessing.ProcessPoolExecutor"],
  "storage"    : "SQLite3",
  "analysis"   : ["pandas", "numpy"],
  "viz"        : ["seaborn", "matplotlib"],
  "topics"     : ["blockchain", "arbitrage", "crypto", "web3",
                  "big-data", "pandas", "yandex", "analytics"]
}
```

---

## `$ git log --oneline`

```
Contributions welcome.

  ┌─────────────────────────────────────────────────┐
  │  git fork → branch → commit → pull request      │
  │  Issues and ideas? Open a GitHub Issue.         │
  └─────────────────────────────────────────────────┘
```

---

## `$ cat LICENSE`

```
MIT License — free to use, modify, and distribute.
© whoIsClownHere  ·  Yandex Big Data Research
```

---

<div align="center">

```
╔══════════════════════════════════════════════════════╗
║   [  BLOCKCHAIN ARBITRAGE ANALYSIS ENGINE  v1.0  ]   ║
║              Session terminated.                     ║
║              Connection closed.                      ║
╚══════════════════════════════════════════════════════╝
```

*Built with 🖤 and async Python*

</div>

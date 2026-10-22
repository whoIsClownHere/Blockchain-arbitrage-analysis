"""Shared paths and helpers for the data scripts."""
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / 'data'
PRICE_DB = DATA_DIR / 'Price_history.sqlite'
TRADES_DB = DATA_DIR / 'Trades_history.sqlite'
ARBITRAGE_TSV = DATA_DIR / 'arbitrage_data.tsv'
ARBITRAGE_TRADES_TSV = DATA_DIR / 'arbitrage_trade_data.tsv'

DEFAULT_START = '2022-11-01 00:00:00'
DEFAULT_END = '2022-11-30 23:59:00'

# Quote currencies we can convert to USDT (via Binance BASE/USDT prices).
CONVERTIBLE_QUOTES = ['BTC', 'ETH', 'SOL']
SUPPORTED_QUOTES = ['USDT'] + CONVERTIBLE_QUOTES


def parse_dt(value):
    return datetime.fromisoformat(value)


def utc_from_ms(ms):
    """Unix milliseconds -> naive UTC datetime."""
    return datetime.fromtimestamp(ms / 1000, timezone.utc).replace(tzinfo=None)


def load_usdt_rates(price_db, start):
    """Binance price of BTC, ETH and SOL in USDT for every hour of the period.

    Returns {'BTC': {'<day>-<hour>': price, ...}, ...}.

    Note: `avg` is never reset, so each value is the running average since
    `start`, not the average of that hour. Kept as-is because the published
    results were produced this way.
    """
    rates = {}
    con = sqlite3.connect(price_db)
    cur = con.cursor()
    for base in CONVERTIBLE_QUOTES:
        rates[base] = {}
        avg = []
        hour_end = start + timedelta(minutes=59)
        rows = cur.execute("SELECT date, open FROM binance WHERE ticker = ?", (f'{base}/USDT',)).fetchall()
        for date, open_price in rows:
            avg.append(open_price)
            if datetime.fromisoformat(date) >= hour_end:
                rates[base][f'{hour_end.day}-{hour_end.hour}'] = round(sum(avg) / len(avg), 2)
                hour_end += timedelta(hours=1)
    con.close()
    return rates

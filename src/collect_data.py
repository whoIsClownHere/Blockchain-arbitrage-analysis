"""Download 1-minute OHLCV candles for every pair on the given exchanges into SQLite.

Each exchange runs in its own process; inside it the tickers are split into
several asyncio groups. Every exchange gets its own table:
ticker, date, open, highest, lowest, close, volume.

Example:
    python src/collect_data.py --exchanges binance huobi mexc lbank2 bitrue whitebit
"""
import argparse
import asyncio
import concurrent.futures
import sqlite3
import sys
import time
from datetime import timedelta
from multiprocessing import cpu_count
from pathlib import Path

import ccxt.async_support

from common import DEFAULT_END, DEFAULT_START, PRICE_DB, parse_dt, utc_from_ms

# Number of asyncio groups per exchange, tuned to stay under rate limits.
GROUPS_PER_EXCHANGE = {'kucoin': 1, 'hitbtc3': 4, 'huobi': 4, 'mexc': 8, 'lbank2': 6, 'bitrue': 8,
                       'whitebit': 8, 'digifinex': 6, 'binance': 6}
DEFAULT_GROUPS = 4

processed = 1


def create_table(cur, table):
    cur.execute(f"CREATE TABLE {table} ('ticker', 'date', 'open', 'highest', 'lowest', 'close', 'volume')")


def insert_candle(cur, table, ticker, date, open_price, highest, lowest, close_price, volume):
    cur.execute(f"INSERT INTO {table} ('ticker', 'date', 'open', 'highest', 'lowest', 'close', 'volume') "
                f"VALUES (?, ?, ?, ?, ?, ?, ?)",
                (ticker, str(date), open_price, highest, lowest, close_price, volume))


async def get_data(proc_id, group_id, con, cur, exchange, exchange_name, tickers, tickers_count, start, end):
    global processed
    if group_id == 1:
        print(f'{exchange_name} started')
    step = 1000
    td = timedelta(hours=16, minutes=40)  # 1000 minutes per request
    td_day = timedelta(days=1)
    td_shift = timedelta()
    if exchange_name == 'bitget':
        step = 100
        td = timedelta(hours=1, minutes=40)
        td_shift = timedelta(hours=15, minutes=1)
    elif exchange_name == 'bitrue':
        td_shift = -timedelta(hours=16, minutes=39)
    elif exchange_name == 'digifinex':
        step = 700
    for ticker in tickers:
        print(ticker)
        date = start - td_shift
        date_now = date
        while date_now <= end:
            from_ts = exchange.parse8601(date.isoformat())
            while True:
                ok = True
                try:
                    if exchange_name == 'bitrue':
                        ohlcv = await exchange.fetch_ohlcv(ticker, '1m', limit=step, params={'fromIdx': from_ts})
                    else:
                        ohlcv = await exchange.fetch_ohlcv(ticker, '1m', since=from_ts, limit=step)
                    break
                except ccxt.errors.RateLimitExceeded:
                    print(exchange_name, 'rate limit exceeded', sep='\t')
                    await asyncio.sleep(2)
                except ccxt.errors.BadSymbol:
                    ok = False
                    break
                except BaseException as e:
                    print(e)
                    ok = False
                    break
            if not ok:
                break
            if len(ohlcv) == 0:
                date += td_day
                date_now = date
                continue
            for candle in ohlcv:
                candle[0] = utc_from_ms(candle[0])
            date_now = ohlcv[-1][0]

            if date_now > end:
                ohlcv = [candle for candle in ohlcv if candle[0] <= end]
            for candle in ohlcv:
                insert_candle(cur, exchange_name, ticker, *candle)
            con.commit()
            date += td
        if group_id == 1:
            print(f'Process {proc_id} processed {processed}/{tickers_count}')
        processed += 1


async def collect(exchange_name, groups, proc_id, start, end, db):
    con = sqlite3.connect(db)
    cur = con.cursor()
    exchange = getattr(ccxt.async_support, exchange_name)()
    exchange.enableRateLimit = False
    await exchange.load_markets()
    create_table(cur, exchange_name)
    symbols = list((await exchange.fetch_tickers()).keys())
    step = max(1, len(symbols) // groups)
    tasks = []
    for group_id, ind in enumerate(range(0, len(symbols), step), 1):
        tasks.append(get_data(proc_id, group_id, con, cur, exchange, exchange_name, symbols[ind:ind + step],
                              len(symbols), start, end))
    await asyncio.gather(*tasks)
    await exchange.close()
    con.close()


def run_exchange(exchange_name, groups, proc_id, start, end, db):
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(collect(exchange_name, groups, proc_id, start, end, db))


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--exchanges', nargs='+', default=['binance'], help='ccxt exchange ids (default: binance)')
    parser.add_argument('--start', default=DEFAULT_START, help=f'first candle, UTC (default: {DEFAULT_START})')
    parser.add_argument('--end', default=DEFAULT_END, help=f'last candle, UTC (default: {DEFAULT_END})')
    parser.add_argument('--db', default=str(PRICE_DB), help='SQLite output (default: data/Price_history.sqlite)')
    args = parser.parse_args()

    start, end = parse_dt(args.start), parse_dt(args.end)
    Path(args.db).parent.mkdir(parents=True, exist_ok=True)
    if cpu_count() < len(args.exchanges):
        print(f'Warning: {len(args.exchanges)} exchanges but only {cpu_count()} CPU cores')

    time_start = time.time()
    with concurrent.futures.ProcessPoolExecutor(len(args.exchanges)) as executor:
        futures = [executor.submit(run_exchange, name, GROUPS_PER_EXCHANGE.get(name, DEFAULT_GROUPS),
                                   proc_id, start, end, args.db)
                   for proc_id, name in enumerate(args.exchanges, 1)]
    for future in futures:
        future.result()
    print(f'Done in {round((time.time() - time_start) / 60, 2)} min')


if __name__ == '__main__':
    main()

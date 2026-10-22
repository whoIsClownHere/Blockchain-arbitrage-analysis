"""Download real trades for pairs listed on all of the given exchanges into SQLite.

The pair list is taken from the price database (pairs that have a candle at
--tickers-date on every exchange). Each exchange runs in its own process and
gets its own table: timestamp, symbol, side, price, amount, cost.

Example:
    python src/collect_data_trades.py --exchanges binance lbank2 --start "2022-11-01 00:00:00" --end "2022-11-01 23:59:00"
"""
import argparse
import concurrent.futures
import sqlite3
import time
from datetime import timezone

import ccxt

from common import DEFAULT_END, PRICE_DB, TRADES_DB, parse_dt


def to_ms(dt):
    return int(dt.replace(tzinfo=timezone.utc).timestamp() * 1000)


def create_table(db, table):
    con = sqlite3.connect(db)
    con.execute(f"CREATE TABLE {table} ('timestamp', 'symbol', 'side', 'price', 'amount', 'cost')")
    con.close()


def insert_trade(cur, table, timestamp, symbol, side, price, amount, cost):
    cur.execute(f"INSERT INTO {table} ('timestamp', 'symbol', 'side', 'price', 'amount', 'cost') "
                f"VALUES (?, ?, ?, ?, ?, ?)",
                (str(timestamp), str(symbol), str(side), str(price), str(amount), str(cost)))


def get_trades(tickers, exchange_name, since_ms, end_ms, db):
    exchange = getattr(ccxt, exchange_name)()
    con = sqlite3.connect(db)
    cur = con.cursor()
    for ind, ticker in enumerate(tickers, 1):
        print(f'{exchange_name} processing {ind}/{len(tickers)}')
        new_date = since_ms
        try:
            while new_date <= end_ms:
                result = exchange.fetch_trades(ticker, since=new_date)
                done = False
                for trade in result:
                    if trade['timestamp'] > end_ms:
                        done = True
                        break
                    insert_trade(cur, exchange_name, trade['timestamp'], trade['symbol'], trade['side'],
                                 trade['price'], trade['amount'], trade['cost'])
                con.commit()
                if result:
                    new_date = result[-1]['timestamp'] + 60_000 if not done else end_ms + 1
                else:
                    new_date += 60_000
        except Exception:
            print('ERROR', exchange_name, ticker, sep='\t')
    con.close()


def collect(tickers, exchange_name, since_ms, end_ms, db):
    create_table(db, exchange_name)
    get_trades(tickers, exchange_name, since_ms, end_ms, db)


def common_tickers(exchanges, price_db, date):
    con = sqlite3.connect(price_db)
    cur = con.cursor()
    sets = [{row[0] for row in cur.execute(f"SELECT ticker FROM {name} WHERE date = ?", (date,)).fetchall()}
            for name in exchanges]
    con.close()
    return sorted(set.intersection(*sets))


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--exchanges', nargs='+', default=['binance', 'lbank2'], help='ccxt exchange ids')
    parser.add_argument('--start', default='2022-11-01 00:00:00', help='first trade, UTC (default: 2022-11-01 00:00:00)')
    parser.add_argument('--end', default='2022-11-01 23:59:00', help='last trade, UTC (default: 2022-11-01 23:59:00)')
    parser.add_argument('--tickers-date', default=DEFAULT_END, help=f'candle time used to pick pairs (default: {DEFAULT_END})')
    parser.add_argument('--prices-db', default=str(PRICE_DB), help='price database (default: data/Price_history.sqlite)')
    parser.add_argument('--db', default=str(TRADES_DB), help='SQLite output (default: data/Trades_history.sqlite)')
    args = parser.parse_args()

    tickers = common_tickers(args.exchanges, args.prices_db, args.tickers_date)
    since_ms, end_ms = to_ms(parse_dt(args.start)), to_ms(parse_dt(args.end))

    time_start = time.time()
    with concurrent.futures.ProcessPoolExecutor(len(args.exchanges)) as executor:
        futures = [executor.submit(collect, tickers, name, since_ms, end_ms, args.db) for name in args.exchanges]
    for future in futures:
        future.result()
    print(f'Done in {round((time.time() - time_start) / 60, 2)} min')


if __name__ == '__main__':
    main()

"""Show how many pairs per exchange are missing from the price database.

For each exchange: number of pairs listed on the exchange minus number of
pairs that have a candle at --date.

Example:
    python src/check_db_data.py --exchanges binance huobi mexc
"""
import argparse
import sqlite3

import ccxt

from common import PRICE_DB

DEFAULT_EXCHANGES = ['binance', 'huobi', 'mexc', 'lbank2', 'bitrue', 'whitebit']


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--exchanges', nargs='+', default=DEFAULT_EXCHANGES, help='ccxt exchange ids')
    parser.add_argument('--date', default='2022-11-01 23:59:00', help='candle time to check (default: 2022-11-01 23:59:00)')
    parser.add_argument('--db', default=str(PRICE_DB), help='price database (default: data/Price_history.sqlite)')
    args = parser.parse_args()

    con = sqlite3.connect(args.db)
    cur = con.cursor()
    for exchange_name in args.exchanges:
        exchange = getattr(ccxt, exchange_name)()
        exchange.load_markets()
        rows = cur.execute(f"SELECT date FROM {exchange_name} WHERE date = ?", (args.date,)).fetchall()
        missing = min(len(exchange.symbols), len(exchange.fetch_tickers())) - len(rows)
        print(exchange_name, missing, sep='\t')
    con.close()


if __name__ == '__main__':
    main()

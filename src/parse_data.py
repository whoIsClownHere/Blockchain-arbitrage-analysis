"""Find arbitrage situations in the 1-minute price database.

For every minute, every ordered pair of exchanges (A, B) and every common
ticker quoted in USDT, BTC, ETH or SOL:
  * buy price  = highest price of the minute on A,
  * sell price = lowest price of the minute on B,
  * spread     = how many percent $100 grows after buying on A and selling on B
                 (non-USDT quotes are converted to USDT via Binance prices).
A spread between 1% and 100% is an arbitrage situation; consecutive minutes
are merged into one situation.

Output TSV columns (comma separated, no header):
spread, start_buy_price, start_sell_price, end_buy_price, end_sell_price,
start_time, end_time, ticker, buy_exchange, sell_exchange

Example:
    python src/parse_data.py --exchanges binance huobi mexc lbank2 bitrue whitebit
"""
import argparse
import sqlite3
from datetime import timedelta

from tqdm import tqdm

from common import (ARBITRAGE_TSV, DEFAULT_END, DEFAULT_START, PRICE_DB, SUPPORTED_QUOTES, load_usdt_rates,
                    parse_dt)

DEFAULT_EXCHANGES = ['binance', 'huobi', 'mexc', 'lbank2', 'bitrue', 'whitebit']
BANK = 100
MIN_SPREAD, MAX_SPREAD = 1, 100
TICKERS_PER_BATCH = 100

rates = {}


def count_spread(date, quote, bank, price_buy, price_sell):
    bank_start = bank
    if quote != 'USDT':
        bank /= rates[quote][f'{date.day}-{date.hour}']
    bank_in_coin = bank / price_buy * price_sell
    if quote != 'USDT':
        bank = bank_in_coin * rates[quote][f'{date.day}-{date.hour}']
    else:
        bank = bank_in_coin
    return round(bank / (bank_start / 100) - 100, 2)


def parse(exchanges, start, end, price_db):
    con = sqlite3.connect(price_db)
    cur = con.cursor()
    data = {}
    situations = {}
    tickers = []
    td = timedelta(minutes=1)
    minutes = int((end - start) / td) + 1

    # Tickers that still trade at the end of the period on at least one exchange.
    for exchange in exchanges:
        for (ticker,) in cur.execute(f"SELECT ticker FROM {exchange} WHERE date = ?", (str(end),)).fetchall():
            if ticker not in tickers:
                tickers.append(ticker)

    for ind in tqdm(range(0, len(tickers), TICKERS_PER_BATCH)):
        batch = tickers[ind:ind + TICKERS_PER_BATCH]
        placeholders = ','.join('?' * len(batch))
        for exchange in exchanges:
            data[exchange] = {}
            rows = cur.execute(f"SELECT ticker, date, highest, lowest FROM {exchange} "
                               f"WHERE ticker IN ({placeholders})", batch).fetchall()
            for ticker, date, highest, lowest in rows:
                dt = parse_dt(date).timestamp()
                data[exchange].setdefault(ticker, {})[dt] = {'buy': highest, 'sell': lowest}

        date = start
        for _ in range(minutes):
            date_key = date.timestamp()
            for exchange1 in exchanges:
                for exchange2 in exchanges:
                    if exchange1 == exchange2:
                        continue
                    for ticker in data[exchange1].keys():
                        if ticker not in data[exchange2]:
                            continue
                        if date_key not in data[exchange1][ticker] or date_key not in data[exchange2][ticker]:
                            continue
                        quote = ticker.split('/')[1]
                        if quote not in SUPPORTED_QUOTES:
                            continue
                        price_buy = data[exchange1][ticker][date_key]['buy']
                        price_sell = data[exchange2][ticker][date_key]['sell']
                        spread = count_spread(date, quote, BANK, price_buy, price_sell)
                        key = f'{exchange1}-{exchange2}-{ticker}'
                        # situation record: [buy, sell, start, [spreads], end, end_buy, end_sell, is_open]
                        if spread < MIN_SPREAD or spread > MAX_SPREAD:
                            if key in situations and situations[key][-1][-1]:
                                situations[key][-1][5] = price_buy
                                situations[key][-1][6] = price_sell
                                situations[key][-1][-1] = False
                            continue
                        if key in situations:
                            if situations[key][-1][4] + td == date:
                                situations[key][-1][4] = date
                                situations[key][-1][3].append(spread)
                            else:
                                situations[key].append([price_buy, price_sell, date, [spread], date, 0, 0, True])
                        else:
                            situations[key] = [[price_buy, price_sell, date, [spread], date, 0, 0, True]]
            date += td
    con.close()
    return situations


def save(situations, out):
    with open(out, mode='w', encoding='utf-8') as file:
        for key, parts in situations.items():
            exchange1, exchange2, ticker = key.split('-')
            for part in parts:
                spread = round(sum(part[3]) / len(part[3]), 3)
                file.write(f'{spread},{part[0]},{part[1]},{part[5]},{part[6]},{part[2].timestamp()},'
                           f'{part[4].timestamp()},{ticker},{exchange1},{exchange2}\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--exchanges', nargs='+', default=DEFAULT_EXCHANGES, help='tables in the price database')
    parser.add_argument('--start', default=DEFAULT_START, help=f'first minute (default: {DEFAULT_START})')
    parser.add_argument('--end', default=DEFAULT_END, help=f'last minute (default: {DEFAULT_END})')
    parser.add_argument('--db', default=str(PRICE_DB), help='price database (default: data/Price_history.sqlite)')
    parser.add_argument('--out', default=str(ARBITRAGE_TSV), help='output (default: data/arbitrage_data.tsv)')
    args = parser.parse_args()

    start, end = parse_dt(args.start), parse_dt(args.end)
    rates.update(load_usdt_rates(args.db, start))
    save(parse(args.exchanges, start, end, args.db), args.out)


if __name__ == '__main__':
    main()

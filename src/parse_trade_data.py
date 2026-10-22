"""Find arbitrage situations in the real trades database.

For every buy trade on exchange A, take the next sell trade on exchange B and
compute the spread the same way as parse_data.py (1% to 100%, $100 bank,
BTC/ETH/SOL quotes converted to USDT). Consecutive profitable trades are
merged into one situation. Output has the same columns as parse_data.py.

Example:
    python src/parse_trade_data.py --exchanges binance lbank2
"""
import argparse
import sqlite3

from tqdm import tqdm

from common import (ARBITRAGE_TRADES_TSV, DEFAULT_START, PRICE_DB, SUPPORTED_QUOTES, TRADES_DB, load_usdt_rates,
                    parse_dt, utc_from_ms)

BANK = 100
MIN_SPREAD, MAX_SPREAD = 1, 100
TICKERS_PER_BATCH = 40

rates = {}


def count_spread(date_buy, date_sell, quote, bank, price_buy, price_sell):
    bank_start = bank
    if quote != 'USDT':
        bank /= rates[quote][f'{date_buy.day}-{date_buy.hour}']
    bank_in_coin = bank / price_buy * price_sell
    if quote != 'USDT':
        bank = bank_in_coin * rates[quote][f'{date_sell.day}-{date_sell.hour}']
    else:
        bank = bank_in_coin
    return round(bank / (bank_start / 100) - 100, 2)


def parse(exchanges, trades_db):
    con = sqlite3.connect(trades_db)
    cur = con.cursor()
    data = {}
    situations = {}
    tickers = []
    for exchange in exchanges:
        for (symbol,) in cur.execute(f"SELECT symbol FROM {exchange}").fetchall():
            if symbol not in tickers:
                tickers.append(symbol)

    for ind in tqdm(range(0, len(tickers), TICKERS_PER_BATCH)):
        batch = tickers[ind:ind + TICKERS_PER_BATCH]
        placeholders = ','.join('?' * len(batch))
        for exchange in exchanges:
            data[exchange] = {}
            rows = cur.execute(f"SELECT timestamp, symbol, side, price FROM {exchange} "
                               f"WHERE symbol IN ({placeholders})", batch).fetchall()
            for timestamp, symbol, side, price in rows:
                trades = data[exchange].setdefault(symbol, {'buy': [], 'sell': []})
                trades[side].append({'date': utc_from_ms(int(timestamp)), 'price': float(price)})

        for exchange1 in exchanges:
            for exchange2 in exchanges:
                if exchange1 == exchange2:
                    continue
                for ticker in data[exchange1].keys():
                    if ticker not in data[exchange2]:
                        continue
                    quote = ticker.split('/')[1]
                    if quote not in SUPPORTED_QUOTES:
                        continue
                    sells = data[exchange2][ticker]['sell']
                    if not sells:
                        continue
                    sell_ind = 0
                    for trade in data[exchange1][ticker]['buy']:
                        date_buy = trade['date']
                        # next sell trade on exchange B after this buy
                        while sell_ind < len(sells) and sells[sell_ind]['date'] <= date_buy:
                            sell_ind += 1
                        if sell_ind >= len(sells):
                            break
                        date_sell = sells[sell_ind]['date']
                        price_buy = trade['price']
                        price_sell = sells[sell_ind]['price']
                        spread = count_spread(date_buy, date_sell, quote, BANK, price_buy, price_sell)
                        key = f'{exchange1}-{exchange2}-{ticker}'
                        # situation record: [buy, sell, start, [spreads], end, end_buy, end_sell, is_open]
                        if spread < MIN_SPREAD or spread > MAX_SPREAD:
                            if key in situations and situations[key][-1][-1]:
                                situations[key][-1][5] = price_buy
                                situations[key][-1][6] = price_sell
                                situations[key][-1][-1] = False
                            continue
                        if key in situations:
                            if situations[key][-1][-1]:
                                situations[key][-1][4] = date_sell
                                situations[key][-1][3].append(spread)
                            else:
                                situations[key].append([price_buy, price_sell, date_buy, [spread],
                                                        date_sell, 0, 0, True])
                        else:
                            situations[key] = [[price_buy, price_sell, date_buy, [spread], date_sell, 0, 0, True]]
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
    parser.add_argument('--exchanges', nargs='+', default=['binance', 'lbank2'], help='tables in the trades database')
    parser.add_argument('--start', default=DEFAULT_START, help=f'start of the price period (default: {DEFAULT_START})')
    parser.add_argument('--db', default=str(TRADES_DB), help='trades database (default: data/Trades_history.sqlite)')
    parser.add_argument('--prices-db', default=str(PRICE_DB), help='price database for USDT rates')
    parser.add_argument('--out', default=str(ARBITRAGE_TRADES_TSV), help='output (default: data/arbitrage_trade_data.tsv)')
    args = parser.parse_args()

    rates.update(load_usdt_rates(args.prices_db, parse_dt(args.start)))
    save(parse(args.exchanges, args.db), args.out)


if __name__ == '__main__':
    main()

import sqlite3
import json
from datetime import datetime, timedelta
from tqdm import tqdm


convert = {}


def collect_convert():
    global convert
    con = sqlite3.connect('Price_history.sqlite')
    cur = con.cursor()
    for ticker in ['BTC/USDT', 'ETH/USDT', 'SOL/USDT']:
        base = ticker.split('/')[0]
        convert[base] = {}
        avg = []
        date = datetime.fromisoformat("2022-11-01 00:59:00")
        td = timedelta(hours=1)
        db_data = cur.execute(f"""SELECT date, open FROM binance WHERE ticker = '{ticker}'""").fetchall()
        for part in db_data:
            date_now = datetime.fromisoformat(part[0])
            if date_now < date:
                avg.append(part[1])
            else:
                avg.append(part[1])
                convert[base][f'{date.day}-{date.hour}'] = round(sum(avg) / len(avg), 2)
                date += td
    con.close()


def prepare(currencies):
    tickers = {}
    for exchange_name in currencies:
        with open(f'blockchain_data/{exchange_name}.json', mode='r', encoding='utf-8') as file:
            tickers[exchange_name] = json.load(file)
    return tickers


def parse(exchanges, currencies):
    con = sqlite3.connect('Price_history.sqlite')
    cur = con.cursor()
    data = {}
    data_situations = {}
    tickers = []
    bank = 100
    for exchange in exchanges:
        db_data = cur.execute(f"""SELECT ticker FROM {exchange} WHERE date = '2022-11-30 23:59:00'""").fetchall()
        for part in db_data:
            if part[0] not in tickers:
                tickers.append(part[0])
    for ind in tqdm(range(0, len(tickers), 100)):
        # parse data
        for exchange in exchanges:
            data[exchange] = {}
            tickers_part = ["'" + i + "'" for i in tickers[ind:ind + 100]]
            db_data = cur.execute(f"""SELECT ticker, date, highest, lowest FROM {exchange}
                                      WHERE ticker in ({','.join(tickers_part)})""").fetchall()
            for part in db_data:
                dt = datetime.fromisoformat(part[1]).timestamp()
                if part[0] not in data[exchange]:
                    data[exchange][part[0]] = {dt: {'buy': part[2], 'sell': part[3]}}
                else:
                    data[exchange][part[0]][dt] = {'buy': part[2], 'sell': part[3]}
        # get all arbitrage situations
        date = datetime.fromisoformat("2022-11-01 00:00:00")
        td = timedelta(minutes=1)
        for _ in range(43200):
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
                        base, quote = ticker.split('/')
                        if quote not in ['USDT', 'SOL', 'BTC', 'ETH']:
                            continue
                        price_buy = data[exchange1][ticker][date_key]['buy']
                        price_sell = data[exchange2][ticker][date_key]['sell']
                        spread = count_spread(date, quote, bank, price_buy, price_sell)
                        key = f'{exchange1}-{exchange2}-{ticker}'
                        if spread < 1 or spread > 100:
                            if key in data_situations and data_situations[key][-1][-1]:
                                data_situations[key][-1][5] = price_buy
                                data_situations[key][-1][6] = price_sell
                                data_situations[key][-1][-1] = False
                            continue
                        if key in data_situations:
                            if data_situations[key][-1][4] + td == date:
                                data_situations[key][-1][4] = date
                                data_situations[key][-1][3].append(spread)
                            else:
                                data_situations[key].append([price_buy, price_sell, date, [spread], date, 0, 0, True])
                        else:
                            data_situations[key] = [[price_buy, price_sell, date, [spread], date, 0, 0, True]]
            date += td
    con.close()
    with open('arbitrage_data.tsv', mode='w', encoding='utf-8') as file:
        for key in data_situations.keys():
            exchange1, exchange2, ticker = key.split('-')
            for part in data_situations[key]:
                spread = round(sum(part[3]) / len(part[3]), 3)
                file.write(f'{spread},{part[0]},{part[1]},{part[5]},{part[6]},{part[2].timestamp()},{part[4].timestamp()},{ticker},{exchange1},{exchange2}\n')


def count_spread(date, quote, bank, price_buy, price_sell):
    bank_start = bank
    if quote != 'USDT':
        bank /= convert[quote][f'{date.day}-{date.hour}']
    bank_in_coin = bank / price_buy * price_sell
    if quote != 'USDT':
        bank = bank_in_coin * convert[quote][f'{date.day}-{date.hour}']
    else:
        bank = bank_in_coin
    return round(bank / (bank_start / 100) - 100, 2)


def main(exchanges):
    collect_convert()
    #currencies = prepare(exchanges)
    parse(exchanges, [])


if __name__ == "__main__":
    main(['binance', 'huobi', 'mexc', 'lbank2', 'bitrue', 'whitebit'])

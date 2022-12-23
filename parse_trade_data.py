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
    con = sqlite3.connect('Trades_history.sqlite')
    cur = con.cursor()
    data = {}
    data_situations = {}
    tickers = []
    bank = 100
    for exchange in exchanges:
        db_data = cur.execute(f"""SELECT symbol FROM {exchange}""").fetchall()
        for part in db_data:
            if part[0] not in tickers:
                tickers.append(part[0])
    for ind in tqdm(range(0, len(tickers), 40)):
        # parse data
        for exchange in exchanges:
            data[exchange] = {}
            tickers_part = ["'" + i + "'" for i in tickers[ind:ind + 40]]
            db_data = cur.execute(f"""SELECT timestamp, symbol, side, price FROM {exchange}
                                      WHERE symbol in ({','.join(tickers_part)})""").fetchall()
            for part in db_data:
                dt = datetime.utcfromtimestamp(int(part[0]) / 1000)
                if part[1] not in data[exchange]:
                    data[exchange][part[1]] = {'buy': [], 'sell': []}
                data[exchange][part[1]][part[2]].append({'date': dt, 'price': float(part[3])})
        # get all arbitrage situations
        a1313 = 1
        for exchange1 in exchanges:
            for exchange2 in exchanges:
                if exchange1 == exchange2:
                    continue
                for ticker in data[exchange1].keys():
                    if ticker not in data[exchange2]:
                        continue
                    base, quote = ticker.split('/')
                    if quote not in ['USDT', 'SOL', 'BTC', 'ETH']:
                        continue
                    ind = 0
                    for trade in data[exchange1][ticker]['buy']:
                        date_buy = trade['date']
                        pr = False
                        while data[exchange2][ticker]['sell'][ind]['date'] <= date_buy:
                            ind += 1
                            if ind >= len(data[exchange2][ticker]['sell']):
                                pr = True
                                break
                        if pr:
                            break
                        date_sell = data[exchange2][ticker]['sell'][ind]['date']
                        price_buy = trade['price']
                        price_sell = data[exchange2][ticker]['sell'][ind]['price']
                        spread = count_spread(date_buy, date_sell, quote, bank, price_buy, price_sell)
                        key = f'{exchange1}-{exchange2}-{ticker}'
                        if spread < 1 or spread > 100:
                            if key in data_situations and data_situations[key][-1][-1]:
                                data_situations[key][-1][5] = price_buy
                                data_situations[key][-1][6] = price_sell
                                data_situations[key][-1][-1] = False
                            continue
                        if key in data_situations:
                            if data_situations[key][-1][-1]:
                                data_situations[key][-1][4] = date_sell
                                data_situations[key][-1][3].append(spread)
                            else:
                                data_situations[key].append([price_buy, price_sell, date_buy, [spread],
                                                             date_sell, 0, 0, True])
                        else:
                            data_situations[key] = [[price_buy, price_sell, date_buy, [spread], date_sell, 0, 0, True]]
    con.close()
    with open('arbitrage_trade_data.tsv', mode='w', encoding='utf-8') as file:
        for key in data_situations.keys():
            exchange1, exchange2, ticker = key.split('-')
            for part in data_situations[key]:
                spread = round(sum(part[3]) / len(part[3]), 3)
                file.write(
                    f'{spread},{part[0]},{part[1]},{part[5]},{part[6]},{part[2].timestamp()},{part[4].timestamp()},'
                    f'{ticker},{exchange1},{exchange2}\n')


def count_spread(date_buy, date_sell, quote, bank, price_buy, price_sell):
    bank_start = bank
    if quote != 'USDT':
        bank /= convert[quote][f'{date_buy.day}-{date_buy.hour}']
    bank_in_coin = bank / price_buy * price_sell
    if quote != 'USDT':
        bank = bank_in_coin * convert[quote][f'{date_sell.day}-{date_sell.hour}']
    else:
        bank = bank_in_coin
    return round(bank / (bank_start / 100) - 100, 2)


def main(exchanges):
    collect_convert()
    # currencies = prepare(exchanges)
    parse(exchanges, [])


if __name__ == "__main__":
    main(['binance', 'lbank2'])

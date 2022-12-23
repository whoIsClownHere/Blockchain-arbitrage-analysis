import ccxt
import sqlite3
from tqdm import tqdm
import time
import concurrent.futures


def get_trades(tickers, exchange_name, since_date):
    exchange_class = getattr(ccxt, exchange_name)
    exchange = exchange_class()

    con = sqlite3.connect('Trades_history.sqlite')
    cur = con.cursor()
    lenn = len(tickers)
    for ind, i in enumerate(tickers, 1):
        print(f'{exchange_name} processing {ind}/{lenn}')
        new_date = since_date
        try:
            while True:
                result = exchange.fetch_trades(i, since=new_date)
                flag = False
                for j in result:
                    if j['timestamp'] > 1667347140000:
                        flag = True
                        break
                    insert_item_to_trades_table(exchange_name, cur, j['timestamp'], j['symbol'], j['side'], j['price'],
                                                j['amount'], j['cost'])

                con.commit()
                if len(result) != 0:
                    new_date = int((j['timestamp'] / 1000 + 60) * 1000)
                else:
                    new_date = int((new_date / 1000 + 60) * 1000)
                if flag:
                    break
        except:
            print('ERROR', exchange_name, i, sep='\t')
    con.close()


def create_bd_table(table):
    con = sqlite3.connect('Trades_history.sqlite')
    cur = con.cursor()

    name = f'{table}'
    cur.execute(f"""CREATE TABLE {name} ('timestamp', 'symbol', 'side', 'price', 'amount', 'cost')""")
    con.close()


def insert_item_to_trades_table(table, cur, timestamp, symbol, side, price, amount, cost):
    cur.execute(f"""INSERT INTO {table} ('timestamp', 'symbol', 'side', 'price', 'amount', 'cost')
                 values('{timestamp}', '{symbol}', '{side}', '{price}', '{amount}', '{cost}')""")


def collect(tickers, exchange_name):
    date = 1667260800000
    create_bd_table(exchange_name)
    get_trades(tickers, exchange_name, date)


def main():
    tickers1 = set()
    tickers2 = set()
    con = sqlite3.connect('Price_history.sqlite')
    cur = con.cursor()
    data = cur.execute(f"""SELECT ticker FROM binance WHERE date='2022-11-30 23:59:00'""").fetchall()
    for part in data:
        tickers1.add(part[0])
    data = cur.execute(f"""SELECT ticker FROM lbank2 WHERE date='2022-11-30 23:59:00'""").fetchall()
    for part in data:
        tickers2.add(part[0])
    tickers = list(tickers1 & tickers2)
    con.close()
    futures = []
    with concurrent.futures.ProcessPoolExecutor(2) as executor:
        new_future = executor.submit(collect, tickers, 'lbank2')
        futures.append(new_future)
        new_future = executor.submit(collect, tickers, 'binance')
        futures.append(new_future)
    concurrent.futures.wait(futures)


if __name__ == '__main__':
    time_start = time.time()
    main()
    print(round((time.time() - time_start) / 60, 2))

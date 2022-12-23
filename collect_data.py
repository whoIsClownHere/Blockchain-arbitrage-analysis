import ccxt.async_support
from datetime import datetime, timedelta
from multiprocessing import cpu_count
import concurrent.futures
import sqlite3
import asyncio
import time


s = 1


def create_bd_table(table, cur):
    name = f'{table}'
    cur.execute(f"""CREATE TABLE {name} ('ticker', 'date', 'open', 'highest', 'lowest', 'close', 'volume')""")


def insert_item_to_table(table, cur, ticker, date, openPrice, highest, lowest, closePrice, volume):
    cur.execute(f"""INSERT INTO {table} ('ticker', 'date', 'open', 'highest', 'lowest', 'close', 'volume')
                 values('{ticker}', '{date}', {openPrice}, {highest}, {lowest}, {closePrice}, {volume})""")


async def get_data(proc_id, id, con, cur, exchange, exchange_name, tickers, tickers_count):
    global s
    if id == 1:
        print(f'{exchange_name} started')
    step = 1000
    td = timedelta(hours=16, minutes=40)
    td_day = timedelta(days=1)
    td_dop = timedelta()
    if exchange_name == 'bitget':
        step = 100
        td = timedelta(hours=1, minutes=40)
        td_dop = timedelta(hours=15, minutes=1)
    elif exchange_name == 'bitrue':
        td_dop = -timedelta(hours=16, minutes=39)
    elif exchange_name == 'digifinex':
        step = 700
    date_end = datetime.fromisoformat("2022-11-30 23:59:00")
    for ticker in tickers:
        print(ticker)
        date = datetime.fromisoformat("2022-11-01 00:00:00") - td_dop
        date_now = date
        while date_now <= date_end:
            since_datetime = date.isoformat()
            from_ts = exchange.parse8601(since_datetime)
            while True:
                pr = True
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
                    pr = False
                    break
                except BaseException as e:
                    print(e)
                    pr = False
                    break
            if not pr:
                break
            if len(ohlcv) == 0:
                date += td_day
                date_now = date
                continue
            for part in ohlcv:
                part[0] = datetime.utcfromtimestamp(part[0] / 1000)
            date_now = ohlcv[-1][0]

            if date_now > date_end:
                ohlcv = list(filter(lambda x: x[0] <= date_end, ohlcv))
            for date_for_insert, openPrice, highest, lowest, closePrice, volume in ohlcv:
                insert_item_to_table(exchange_name, cur, ticker, date_for_insert, openPrice, highest, lowest,
                                     closePrice, volume)
            con.commit()
            date += td
        # print(f'Group {id} processed ticker {s}')
        if id == 1:
            print(f'Process {proc_id} processed {s}/{tickers_count}')
        s += 1


async def collect(exchanges, d, proc_id):
    con = sqlite3.connect('Price_history.sqlite')
    cur = con.cursor()
    for exchange_name in exchanges:
        exchange_class = getattr(ccxt.async_support, exchange_name)
        exchange = exchange_class()
        exchange.enableRateLimit = False
        await exchange.load_markets()
        create_bd_table(exchange_name, cur)
        symbols1 = await exchange.fetch_tickers()
        symbols = list(symbols1.keys())
        tasks = []
        step = len(symbols) // d
        id = 1
        for ind in range(0, len(symbols), step):
            tasks.append(get_data(proc_id, id, con, cur, exchange, exchange_name, symbols[ind:ind + step],
                                  len(symbols)))
            id += 1
        await asyncio.gather(*tasks)
        await exchange.close()
    con.close()


def prepare_to_collect(exchanges, d, proc_id):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(collect(exchanges, d, proc_id))


def main(exchanges):
    cores_count = cpu_count()
    exchanges_groups_count_recomend = {'kucoin': 1, 'hitbtc3': 4, 'huobi': 4, 'mexc': 8, 'lbank2': 6, 'bitrue': 8,
                                       'whitebit': 8, 'digifinex': 6, 'binance': 6}
    futures = []
    if cores_count < 10:
        print('At least 10 cores required')
        return
    with concurrent.futures.ProcessPoolExecutor(len(exchanges)) as executor:
        for proc_id, exchange_name in enumerate(exchanges, 1):
            # print(f'process №{ind_of_process}', end='\t')
            new_future = executor.submit(prepare_to_collect, [exchange_name],
                                         exchanges_groups_count_recomend[exchange_name], proc_id)
            futures.append(new_future)
    concurrent.futures.wait(futures)


if __name__ == "__main__":
    time_start = time.time()
    main(['binance'])
    print(round((time.time() - time_start) / 60, 2))

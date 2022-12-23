import sqlite3
import ccxt


def main(exchange_names):
    con = sqlite3.connect('Price_history.sqlite')
    cur = con.cursor()
    for exchange_name in exchange_names:
        exchange_class = getattr(ccxt, exchange_name)
        exchange = exchange_class()
        exchange.load_markets()
        data = cur.execute(f"""SELECT date FROM {exchange_name} WHERE date = '2022-11-01 23:59:00'""").fetchall()
        print(exchange_name, min([len(exchange.symbols), len(exchange.fetch_tickers())]) - len(data))
    con.close()


if __name__ == '__main__':
    main(['binance', 'huobi', 'mexc', 'lbank2', 'bitrue', 'whitebit'])

# Аналитика блокчейн-арбитража

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Jupyter](https://img.shields.io/badge/Jupyter-Notebook-F37626?logo=jupyter&logoColor=white)](arbitrage_analysis.ipynb)
[![ccxt](https://img.shields.io/badge/ccxt-exchange_API-000000)](https://github.com/ccxt/ccxt)
[![SQLite](https://img.shields.io/badge/SQLite-storage-003B57?logo=sqlite&logoColor=white)](https://sqlite.org/)

Собрали минутные цены всех торговых пар с шести криптобирж за ноябрь 2022, нашли почти **миллион арбитражных ситуаций** и проверили две стратегии заработка на них: классическую (купить → перевести → продать) и новую (long + short без перевода токена).

Весь анализ — в одном ноутбуке: **[arbitrage_analysis.ipynb](arbitrage_analysis.ipynb)**. Презентация — [Big Data presentation.pdf](Big%20Data%20presentation.pdf).

## Главное

| | |
|---|---|
| Период и данные | 1–30 ноября 2022, минутные свечи (OHLCV) |
| Биржи | Binance, Huobi, MEXC, LBank, Bitrue, WhiteBIT |
| Найдено арбитражных ситуаций | **976 521** |
| Средний spread | **2.45%** |
| Средняя длительность ситуации | **23 мин 45 с** |
| Классическая стратегия, $100 × 1000 сделок за месяц | **$2 552 – $2 957** прибыли |
| Новая стратегия, $100 × 1000 сделок за месяц | **$2 101 – $3 048** прибыли |
| Успешность новой стратегии | long — **85.0%**, short — **86.7%** |

Прибыль — 95% интервал по симуляции (случайная выборка 1000 ситуаций, много повторов), без учёта комиссий.

## Как это работает

```mermaid
flowchart LR
    API["API бирж<br/>(ccxt)"] -->|collect_data.py| DB[("Price_history.sqlite<br/>минутные свечи")]
    DB -->|parse_data.py| ARB["arbitrage_data.tsv<br/>арбитражные ситуации"]
    API -->|collect_data_trades.py| TDB[("Trades_history.sqlite<br/>реальные трейды")]
    TDB -->|parse_trade_data.py| TARB["arbitrage_trade_data.tsv"]
    ARB --> NB["arbitrage_analysis.ipynb"]
    TARB --> NB
```

### 1. Сбор данных

[collect_data.py](collect_data.py) скачивает через `fetch_ohlcv` из [ccxt](https://github.com/ccxt/ccxt) минутные свечи по **всем** парам биржи. Каждая биржа обрабатывается в отдельном процессе, внутри — несколько asyncio-групп тикеров. Для каждой биржи подобраны размер запроса и число групп, чтобы не упираться в rate limit. Данные складываются в SQLite: одна таблица на биржу, колонки `ticker, date, open, highest, lowest, close, volume`.

[check_db_data.py](check_db_data.py) проверяет, по скольким парам данные не скачались.

![Алгоритм получения данных](images/slide_data_collection.png)

### 2. Поиск арбитражных ситуаций

[parse_data.py](parse_data.py) проходит по каждой минуте месяца (43 200 минут), каждой паре бирж и каждому общему тикеру:

- **Цена покупки** на бирже A — максимум минутной свечи, **цена продажи** на бирже B — минимум. Это пессимистичная оценка: берём худшие цены за минуту.
- **Spread** — на сколько процентов вырастут $100, если купить токен на A и продать на B.
- Пары к BTC, ETH и SOL переводятся в доллары по среднечасовому курсу на Binance, поэтому все спреды сравнимы.
- Ситуацией считаем **spread от 1% до 100%**. Подряд идущие минуты с таким спредом склеиваются в одну ситуацию.

Для каждой ситуации сохраняются средний spread, цены на старте и в конце, время начала и конца, тикер и пара бирж. Данных немного, поэтому результат пишется в TSV — его легко открыть в pandas.

### 3. Реальные трейды

[collect_data_trades.py](collect_data_trades.py) и [parse_trade_data.py](parse_trade_data.py) делают то же самое по реальным сделкам (а не свечам) для Binance и LBank за 1 ноября 2022. Это нужно, чтобы проверить, насколько ситуации на минутных данных реальны.

## Результаты

### Общая аналитика

**Spread во времени.** Спреды есть весь месяц, особенно много крупных — 8–11 ноября, во время краха FTX.

![Spread и время начала арбитража](images/spread_over_time.png)

| Как часто встречается spread | Spread от длительности ситуации |
|---|---|
| ![](images/spread_frequency.png) | ![](images/spread_vs_duration.png) |
| По X — число ситуаций, по Y — spread. Spread 1–1.5% встречается намного чаще, чем 4–4.5%. | Чем больше spread, тем дольше обычно держится ситуация. |

| Длительность ситуаций | Котируемые валюты |
|---|---|
| ![](images/duration_distribution.png) | ![](images/quote_count.png) |
| Среди ситуаций дольше 5 минут большинство длится 5–30 минут. | Чаще всего арбитраж в парах к USDT, затем BTC и ETH. |

**Схождение цен.** Разница конечных цен токена на двух биржах почти всегда около нуля: к концу ситуации цены сходятся. На этом построена новая стратегия.

![Проверка на схождение цен](images/price_convergence.png)

**Биржи.** Чаще всего выгодно покупать на MEXC и Huobi. Средний spread по биржам близок: 1.5–1.9%.

| Число ситуаций по бирже покупки | Средний spread по бирже покупки |
|---|---|
| ![](images/buy_exchange_count.png) | ![](images/buy_exchange_mean_spread.png) |

### Классическая стратегия

![Классическая стратегия](images/slide_classic_strategy.png)

Покупаем токен там, где он дешевле, переводим на другую биржу и продаём дороже. Перевод занимает время, поэтому ситуация должна прожить хотя бы 15 минут.

- Ситуаций длительностью 3–15 минут (перевод не успеет): **220 557** — невыгодные.
- Ситуаций от 15 минут: **158 446** — выгодные.
- 1000 сделок по $100 за месяц приносят **$2 552 – $2 957**.

### Новая стратегия

![Новая стратегия](images/slide_new_strategy.png)

Токен не переводим. На дешёвой бирже открываем long, на дорогой — short, и ждём, пока цены сойдутся. Так не нужно ждать перевод, и можно брать короткие ситуации (от 2 минут).

| Long на бирже покупки | Short на бирже продажи |
|---|---|
| ![](images/new_strategy_long.png) | ![](images/new_strategy_short.png) |
| **85.0%** сделок успешны | **86.7%** сделок успешны |

Красные точки — сделки, где цена пошла против позиции.

1000 сделок по $100 за месяц (только пары к USDT) приносят **$2 101 – $3 048**: разброс шире, чем у классической, но верхняя граница выше.

### Минутные свечи против реальных трейдов

Сравнили одинаковый срез (1 ноября, покупка на Binance или LBank) по свечам и по реальным сделкам:

| | Свечи | Трейды |
|---|---|---|
| Средний spread | 1.71% | 1.31% |
| Средняя длительность | 73 мин | 27 мин |

| Как часто встречается spread (слева свечи, справа трейды) | Ситуации по времени суток (слева свечи, справа трейды) |
|---|---|
| ![](images/compare_spread_frequency.png) | ![](images/compare_time_of_day.png) |

По реальным сделкам спреды меньше и живут почти втрое короче. Часть ситуаций на минутных свечах нереализуема из-за низкой ликвидности, поэтому перед сделкой нужно проверять стакан.

## Ограничения

- Прибыль считается без комиссий бирж, комиссии за перевод и проскальзывания.
- Минутные свечи завышают спред и длительность ситуаций по сравнению с реальными трейдами.
- Ноябрь 2022 — нетипичный месяц из-за краха FTX.

## Структура репозитория

```
├── arbitrage_analysis.ipynb   # весь анализ: общая аналитика, обе стратегии, сравнение с трейдами
├── collect_data.py            # сбор минутных свечей → Price_history.sqlite
├── check_db_data.py           # проверка полноты собранных данных
├── parse_data.py              # поиск арбитражных ситуаций → arbitrage_data.tsv
├── collect_data_trades.py     # сбор реальных трейдов Binance и LBank → Trades_history.sqlite
├── parse_trade_data.py        # поиск ситуаций по трейдам → arbitrage_trade_data.tsv
├── images/                    # графики из ноутбука и схемы из презентации
├── Big Data presentation.pdf  # презентация проекта
└── requirements.txt
```

## Запуск

```bash
git clone https://github.com/whoIsClownHere/Blockchain-arbitrage-analysis.git
cd Blockchain-arbitrage-analysis
pip install -r requirements.txt

python collect_data.py         # список бирж — в main(); нужно 10+ ядер
python parse_data.py
python collect_data_trades.py
python parse_trade_data.py

mkdir -p Datasets && mv arbitrage_data.tsv arbitrage_trade_data.tsv Datasets/
jupyter notebook arbitrage_analysis.ipynb
```

Сбор данных идёт долго: скрипты скачивают историю по всем парам каждой биржи. `collect_data.py` написан под Windows (`WindowsSelectorEventLoopPolicy`); на macOS и Linux эту строку нужно убрать.

## Авторы

- **Егор Ермаков** — [@whoIsClownHere](https://github.com/whoIsClownHere)
- **Михаил Шершнев** — [@mish1ps](https://github.com/mish1ps)

Ментор — Дмитрий.

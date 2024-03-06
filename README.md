# Blockchain-arbitration

Подробный анализ ситуаций блокчейн-арбитража включает в себя несколько ключевых этапов, начиная с сбора данных с различных бирж, анализа спреда, сравнения и расчета рисков двух прибыльных стратегий. Этот процесс требует использования специализированных инструментов и технологий для эффективного выполнения.

Сбор данных с разных бирж: Для начала необходимо собрать данные о ценах на активы на различных биржах. Это можно сделать с помощью библиотеки ccxt, которая предоставляет универсальный API для взаимодействия с множеством криптовалютных бирж. Скрипты collect_data.py и collect_data_trades.py в проекте на GitHub используются для сбора минутных данных за месяц и данных о транзакциях за день соответственно.
Анализ спреда: Спред (разница между максимальной и минимальной ценой за актив) является ключевым показателем для определения потенциальных возможностей для арбитража. Сбор данных о спреде помогает определить, какие активы имеют наибольший потенциал для арбитража.
Сравнение и расчет рисков двух прибыльных стратегий: В проекте представлены два файла анализа стратегий (analis_strategy_classic.ipynb и analis_strategy_new.ipynb), которые детально изучают две прибыльные стратегии арбитража. Сравнение этих стратегий и расчет их рисков помогает выбрать наиболее эффективную стратегию для арбитража.
Технологии и инструменты: Проект использует различные технологии и библиотеки Python, такие как pandas, numpy, seaborn, sql, matplotlib.pyplot, asyncio и tqdm, для анализа данных, визуализации и асинхронного выполнения задач. Эти инструменты позволяют эффективно обрабатывать большие объемы данных и выполнять сложные расчеты.
Проект на GitHub: Репозиторий на GitHub содержит все необходимые файлы и код для выполнения анализа блокчейн-арбитража, включая скрипты для сбора данных, анализа, сравнения стратегий и визуализации результатов. Это делает проект доступным и легко воспроизводимым для других исследователей и разработчиков.
В целом, подробный анализ ситуаций блокчейн-арбитража требует глубокого понимания рынка, использования современных технологий для обработки данных и критического мышления при выборе и оценке потенциальных стратегий.


## About files
<ul>
  <li>analis_strategy_classic.ipynb - File in which the classic strategy is analyzed</li>
  <li>analis_strategy_new.ipynb - File in which the classic strategy is analyzed</li>
  <li>check_db_data.py - File in which the integrity of the collected data is checked</li>
  <li>collect_data.py - File that collects minute data for a month</li>
  <li>collect_data_trades.py - File that collects data on transactions per day</li>
  <li>comparison.ipynb - Comparison of arbitrage situations collected on minute data and on trade data</li>
  <li>data_analise.ipynb - Dataset analysis</li>
  <li>parse_data.py - Collection of arbitrage situations from minute data</li>
  <li>parse_trade_data.py - Collection of arbitrage situations from trade data</li>
</ul>

## Technologies
<ul>
  <li>ccxt</li>
  <li>pandas</li>
  <li>numpy</li>
  <li>seaborn</li>
  <li>sql</li>
  <li>matplotlib.pyplot</li>
  <li>asyncio</li>
  <li>tqdm</li>
</ul>

# Hyperliquid Funding Rates

Этот проект содержит функции для получения информации о perpetual маркетах с Hyperliquid и отображения топ-10 маркетов, отсортированных по funding rate.

## Установка зависимостей

```bash
pip install ccxt requests pandas
```

## Использование

### Основная функция

```python
from connectors.hyperliquid import get_hyperliquid_funding_rates_direct, print_funding_rates_table

# Получаем данные
funding_rates = get_hyperliquid_funding_rates_direct()

# Выводим таблицу
print_funding_rates_table(funding_rates)
```

### Запуск примера

```bash
python example_usage.py
```

### Запуск теста

```bash
python test_hyperliquid.py
```

## Функции

### `get_hyperliquid_funding_rates_direct()`

Получает funding rates напрямую через Hyperliquid API. Возвращает список словарей с информацией о маркетах:

```python
[
    {
        'symbol': 'BTC',
        'funding_rate': 0.0001,  # 0.01%
        'volume_24h': 1000000,   # $1M
        'next_funding': 'TODO'
    },
    # ...
]
```

### `print_funding_rates_table(funding_rates)`

Выводит красивую таблицу с funding rates:

```
📊 HYPERLIQUID FUNDING RATES (TOP 10)
============================================================
Symbol       Funding Rate    Next Funding    24h Volume     
------------------------------------------------------------
🟢 LAUNCHCOIN    0.0062%      TODO            $1000K         
⚪ BTC       0.0013%      TODO            $1000K         
⚪ ETH       0.0013%      TODO            $1000K         
...
```

## Цветовое кодирование

- 🟢 - Funding rate > 0.01%
- 🟡 - Funding rate > 0.001%
- ⚪ - Funding rate ≤ 0.001%

## Структура проекта

```
eth-global-2025/
├── connectors/
│   ├── hyperliquid.py    # Основные функции для работы с Hyperliquid
│   └── hliq.py          # Существующий connector
├── main.py              # Основной файл проекта
├── example_usage.py     # Пример использования
├── test_hyperliquid.py  # Тестовый скрипт
└── README.md           # Этот файл
```

## API Endpoints

Функция использует официальный API Hyperliquid:
- `https://api.hyperliquid.xyz/info` - для получения метаданных и funding rates
- `https://api.hyperliquid.xyz/info` - для получения информации о торговле

## Обработка ошибок

Функция включает обработку ошибок и fallback механизмы:
1. Сначала пытается использовать прямой API вызов
2. Если не удается, пробует через ccxt
3. Возвращает пустой список в случае ошибки

## Требования

- Python 3.7+
- ccxt
- requests
- pandas (опционально) 
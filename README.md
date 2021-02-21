# Binance order bot

Built to easily allow the creation of limit orders


## Setup
- Install Python3 and pip
- Create virtualenv.. optional (`python3 -m venv venv ; source venv/bin/activate.sh`)
- `python3 -m pip install requirements.txt`
- Create Binance API key
- Place API key into `data/user.yml`


## Usage
!! No order will be created unless the `--execute` flag is provided

Create buy order:

```
python order.py create-order buy NANOUSDT --start-price 6.55 --quantity 300 --ladder-percent 1 --ladder-orders 20
```

Create sell order:

```
python order.py create-order sell NANOUSDT --start-price 6.55 --quantity 300 --ladder-percent 1 --ladder-orders 20
```

These will print a dry run of what would be created, add `--execute` to create them.
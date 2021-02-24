import os
import yaml
import math
import argparse
from decimal import Decimal
from binance.exceptions import BinanceAPIException
from functools import cache
from binance.client import Client

with open("./data/config.yml") as f:
    config = yaml.load(f, Loader=yaml.SafeLoader)
client = Client(config["binance"]["api_key"], config["binance"]["api_secret_key"])

parser = argparse.ArgumentParser("Binance order creator")

subparser = parser.add_subparsers(dest="command")

common = argparse.ArgumentParser(add_help=False)
common.add_argument("--execute", action="store_true", help="Create the orders")

parser_create_order = subparser.add_parser(
    "create-order", help="Create order", parents=[common]
)
parser_create_order.add_argument("order_type", choices=["buy", "sell"])
parser_create_order.add_argument("pair", help="e.g. ETHUSDT")
parser_create_order.add_argument(
    "--start-price", help="Price to start ladder at", type=Decimal, required=True
)
group = parser_create_order.add_mutually_exclusive_group(required=True)
group.add_argument(
    "--quantity", help="Quantity of asset to buy", type=Decimal
)
group.add_argument(
    "--quote-quantity", help="Quantity of quote to use to buy asset", type=Decimal
)
parser_create_order.add_argument(
    "--ladder-percent", help="Ladder gap %", default=1, type=Decimal
)
parser_create_order.add_argument(
    "--ladder-orders", help="How many orders to create", default=5, type=int
)

parser_exit_quick = subparser.add_parser(
    "exit-quick", help="Exit positions quickly with limit orders", parents=[common]
)
parser_exit_quick.add_argument("--pair", help="e.g. ETHUSDT")

parser_balance = subparser.add_parser("balances", help="Balances", parents=[common])

args = parser.parse_args()


@cache
def get_precision(pair):
    info = client.get_symbol_info(pair.upper())
    filters = info["filters"]
    step_size = float(
        [f for f in filters if f["filterType"] == "LOT_SIZE"][0]["stepSize"]
    )
    return int(round(-math.log(step_size, 10), 0))


def order_limit(quantity, price):
    print(f"{args.pair} - {args.order_type} {quantity} @ {price} ({price * Decimal(str(quantity))})")
    if args.execute:
        if args.order_type == "buy":
            order = client.order_limit_buy(
                symbol=args.pair,
                quantity=quantity,
                price=price,
            )
        elif args.order_type == "sell":
            order = client.order_limit_sell(
                symbol=args.pair,
                quantity=quantity,
                price=price,
            )

def get_precision(pair):
    info = client.get_symbol_info(pair.upper())
    filters = info["filters"]
    step_size = float(
        [f for f in filters if f["filterType"] == "LOT_SIZE"][0]["stepSize"]
    )
    precision = int(round(-math.log(step_size, 10), 0))
    return precision

def create_ladder_order_quantity(
    pair, order_type, start_price, quantity, ladder_percent, ladder_orders
):
    total_cost = start_price * quantity
    order_quantity = quantity / ladder_orders
    ladder_gap = start_price * Decimal(ladder_percent / 100)
    if args.order_type == "sell":
        ladder_gap = -ladder_gap

    print(f"{order_quantity=} per order")
    print(f"{total_cost=}")
    print(f"{ladder_gap=}")

    ladder_price = args.start_price
    for _ in range(args.ladder_orders):
        order_limit(order_quantity, ladder_price)
        ladder_price -= ladder_gap

def create_ladder_order_quote_quantity(
    pair, order_type, start_price, quote_quantity, ladder_percent, ladder_orders
):
    factor = 10 ** get_precision(pair)
    # target_quantity = math.floor(target_quantity * factor) / factor

    # total_cost = start_price * quote_quantity
    quote_quantity = quote_quantity / ladder_orders
    ladder_gap = start_price * Decimal(ladder_percent / 100)
    if args.order_type == "sell":
        ladder_gap = -ladder_gap
    # print(quote_quantity, ladder_gap)

    # print(f"{order_quantity=} per order")
    # print(f"{total_cost=}")
    print(f"{ladder_gap=}")

    cost = 0
    ladder_price = args.start_price
    for _ in range(args.ladder_orders):
        order_quantity = math.floor((quote_quantity / ladder_price) * factor) / factor
        order_limit(order_quantity, ladder_price)
        cost += (Decimal(str(order_quantity)) * ladder_price)
        ladder_price -= ladder_gap

def exit_quick(pair, pct_above=0.01):
    info = client.get_symbol_info(pair)
    base = info["baseAsset"]
    balance = client.get_asset_balance(asset=base)
    if float(balance["locked"]) > 0:
        print("Will close all positions:")
        orders = client.get_open_orders(symbol=pair)
        [print(f"{order['origQty']} @ {order['price']}") for order in orders]

        ok = input("Continue? [Y\\n]").lower() == "y"
        if ok:
            [
                client.cancel_order(symbol=pair, orderId=order["orderId"])
                for order in orders
            ]

    balance = client.get_asset_balance(asset=base)
    print(f"Exiting {balance['free']} {base} quickly")


def fetch_balances():
    info = client.get_account()
    [
        print(bal)
        for bal in info["balances"]
        if float(bal["free"]) > 0 or float(bal["locked"]) > 0
    ]


if args.command == "create-order":
    if args.quantity:
        create_ladder_order_quantity(
            args.pair,
            args.order_type,
            args.start_price,
            args.quantity,
            args.ladder_percent,
            args.ladder_orders,
        )
    else:
        create_ladder_order_quote_quantity(
            args.pair,
            args.order_type,
            args.start_price,
            args.quote_quantity,
            args.ladder_percent,
            args.ladder_orders,
        )
elif args.command == "exit-quick":
    exit_quick(args.pair)
elif args.command == "balances":
    fetch_balances()

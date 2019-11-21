import ccxt
import time
import json
import requests
import pandas as pd
import datetime as dt
from datetime import timedelta
from exchange import exchange
from notification import notificator
from requests.adapters import HTTPAdapter

show_error = "YES"

exchange = exchange()


def check_coin_price(coin_pair):
    try:
        last_price = exchange.fetch_ticker(coin_pair)["last"]

        if last_price != None:
            return last_price
        else:
            notificator("price is None, get error, check_coin_price 24")

    except ccxt.NetworkError as e:
        if show_error == "YES":
            notificator(str(e))
    except ccxt.ExchangeError as e:
        if show_error == "YES":
            notificator(str(e))
    except Exception as e:
        if show_error == "YES":
            notificator(str(e) + "get error, check_coin_price 34")


def get_bars(symbol, interval):
    root_url = "https://api.binance.com/api/v1/klines"
    user_agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.47 Safari/537.36"
    url = root_url + "?symbol=" + symbol + "&interval=" + interval

    req_session = requests.Session()
    req_session.headers.update({"User-Agent": user_agent})
    req_session.mount(url, HTTPAdapter(max_retries=19))

    try:
        while True:
            req = req_session.get(url, headers={"User-Agent": user_agent})

            if req.ok:
                data = json.loads(req.text)

                df = pd.DataFrame(data)
                df.columns = [
                    "open_time",
                    "open",
                    "high",
                    "low",
                    "close",
                    "volume",
                    "close_time",
                    "qav",
                    "num_trades",
                    "taker_base_vol",
                    "taker_quote_vol",
                    "ignore",
                ]
                df.index = [
                    dt.datetime.fromtimestamp(x / 1000.0) for x in df.close_time
                ]
                df.open = df.open.astype(float)
                df.close = df.close.astype(float)

                return df
                break

            else:
                notificator(
                    "df type:"
                    + str(type(df))
                    + "data type:"
                    + str(type(data))
                    + "req.text:"
                    + str(req.text)
                    + "from get_bars (while loop else)"
                )
                continue

    except Exception as e:
        if show_error == "YES":
            notificator(
                str(e)
                + "df type:"
                + str(type(df))
                + "data type:"
                + str(type(data))
                + "req.text:"
                + str(req.text)
                + "from market_data.py (get_bars Exception)"
            )

import time
from config import get_config
from market_data import check_coin_price, get_bars
from notification import notificator
from ignore_signals import (
    ignore_buy_signal_times,
    ignore_sell_signal_times,
    ingnore_signal_time,
)
from human import number_for_human
from exchange import api_requests_frequency

show_error = "YES"
debug = "NO"

api_requests_frequency = api_requests_frequency()
buy_indicators_type = get_config()["buy_indicators_type"]
sell_indicators_type = get_config()["sell_indicators_type"]
indicators_bb_period = int(get_config()["indicators_bb_period"])
indicators_rsi_period = int(get_config()["indicators_rsi_period"])
buy_indicators_timeframe = get_config()["buy_indicators_timeframe"]
sell_indicators_timeframe = get_config()["sell_indicators_timeframe"]
rsi_buy_level = int(get_config()["rsi_buy_level"])
rsi_sell_level = int(get_config()["rsi_sell_level"])
price_buffer = float(get_config()["price_buffer_for_start_sell_on_sell_signal"])
use_stop_loss_while_start_sell_on_sell_signal = get_config()[
    "use_stop_loss_while_start_sell_on_sell_signal"
]
stop_loss_percent_for_start_sell_on_sell_signal = float(
    get_config()["stop_loss_percent_for_start_sell_on_sell_signal"]
)


def bollingerband(coin_pair_for_get_bars, timeframe):
    def get_bb():
        try:
            df = get_bars(coin_pair_for_get_bars, timeframe)
            sma = (
                df["close"]
                .rolling(window=indicators_bb_period, min_periods=indicators_bb_period - 1)
                .mean()
            )
            std = (
                df["close"]
                .rolling(window=indicators_bb_period, min_periods=indicators_bb_period - 1)
                .std()
            )
            up = (sma + (std * 2)).to_frame("BBANDUP")
            lower = (sma - (std * 2)).to_frame("BBANDLO")
            bollingerband = df.join(up).join(lower)
            bollingerband = bollingerband.dropna()
            bollingerband_low = bollingerband["BBANDLO"][-1]
            bollingerband_up = bollingerband["BBANDUP"][-1]

            return bollingerband_low, bollingerband_up

        except Exception:
            pass

    while True:
        bb = get_bb()
        if str(type(bb)) != "<class 'NoneType'>":
            bollingerband_low, bollingerband_up = bb
            return bollingerband_low, bollingerband_up
            break
        else:
            continue


def rsi(coin_pair_for_get_bars, timeframe):
    def get_rsi():
        try:
            df = get_bars(coin_pair_for_get_bars, timeframe)
            delta = df.close.diff()
            up_days = delta.copy()
            up_days[delta <= 0] = 0.0
            down_days = abs(delta.copy())
            down_days[delta > 0] = 0.0
            RS_up = up_days.rolling(indicators_rsi_period).mean()
            RS_down = down_days.rolling(indicators_rsi_period).mean()
            rsi = 100 - 100 / (1 + RS_up / RS_down)
            rsi_data = rsi.dropna()
            rsi_now = rsi_data[-1]

            return rsi_now

        except Exception:
            pass

    while True:
        rsi_now = get_rsi()
        if str(type(rsi_now)) != "<class 'NoneType'>":
            return rsi_now
            break
        else:
            continue


#################################################################################


def get_signals_from_external_system():
    pass


#################################################################################


def get_indicators_signal(coin, coin_2):
    coin_pair_for_get_bars = (
        coin + coin_2
    )  # another format(ETHBTC) then coin_pair(ETH/BTC) for ccxt

    try:
        while True:
            if buy_indicators_type == "RSI+BB":
                coin_price = check_coin_price(coin_pair_for_get_bars)
                bb_low = bollingerband(
                    coin_pair_for_get_bars, buy_indicators_timeframe
                )[0]
                rsi_data_now = rsi(coin_pair_for_get_bars, buy_indicators_timeframe)

                if coin_price < bb_low and rsi_data_now < rsi_buy_level:

                    notificator(
                        "Pair "
                        + str(coin_pair_for_get_bars)
                        + "\n"
                        + "Price "
                        + str(number_for_human(coin_price))
                        + "\n"
                        + "BB low "
                        + str(number_for_human(bb_low))[:9]
                        + "\n"
                        + "RSI "
                        + str(rsi_data_now)[:9]
                        + "\n"
                        + "Timeframe "
                        + str(buy_indicators_timeframe)
                        + "\n"
                        + "BUY"
                    )

                    signal = {
                        "pair": coin_pair_for_get_bars,
                        "price": coin_price,
                        "bb_low": bb_low,
                        "rsi_data_now": rsi_data_now,
                        "signal": "BUY",
                    }

                    if get_config()["ignore_buy_signal_enable"] == "YES":

                        if get_config()["ignore_buy_signal_type"] == "time":
                            return ingnore_signal_time(
                                signal, int(get_config()["ignore_buy_signal_time_sec"])
                            )
                            break

                        if get_config()["ignore_buy_signal_type"] == "times":
                            if (
                                ignore_buy_signal_times(
                                    signal, int(get_config()["ignore_buy_signal_times"])
                                )
                                == "OK"
                            ):
                                return signal
                                break
                    else:
                        return signal
                        break

                else:
                    if debug == "YES":
                        notificator("Awaiting for Signal ...")
                    time.sleep(api_requests_frequency)
                    continue

            if buy_indicators_type == "RSI":
                coin_price = check_coin_price(coin_pair_for_get_bars)
                rsi_data_now = rsi(coin_pair_for_get_bars, buy_indicators_timeframe)

                if rsi_data_now < rsi_buy_level:

                    notificator(
                        "Pair "
                        + str(coin_pair_for_get_bars)
                        + "\n"
                        + "RSI "
                        + str(rsi_data_now)[:9]
                        + "\n"
                        + "Timeframe "
                        + str(buy_indicators_timeframe)
                        + "\n"
                        + "BUY"
                    )
                    signal = {
                        "pair": coin_pair_for_get_bars,
                        "price": coin_price,
                        "rsi_data_now": rsi_data_now,
                        "signal": "BUY",
                    }

                    if get_config()["ignore_buy_signal_enable"] == "YES":

                        if get_config()["ignore_buy_signal_type"] == "time":
                            return ingnore_signal_time(
                                signal, int(get_config()["ignore_buy_signal_time_sec"])
                            )
                            break

                        if get_config()["ignore_buy_signal_type"] == "times":
                            if (
                                ignore_buy_signal_times(
                                    signal, int(get_config()["ignore_buy_signal_times"])
                                )
                                == "OK"
                            ):
                                return signal
                                break
                    else:
                        return signal
                        break

                else:
                    if debug == "YES":
                        notificator("Awaiting for Signal ...")
                    time.sleep(api_requests_frequency)
                    continue

            if buy_indicators_type == "BB":
                coin_price = check_coin_price(coin_pair_for_get_bars)
                bb_low = bollingerband(
                    coin_pair_for_get_bars, buy_indicators_timeframe
                )[0]

                if coin_price < bb_low:

                    notificator(
                        "Pair "
                        + str(coin_pair_for_get_bars)
                        + "\n"
                        + "Price "
                        + str(number_for_human(coin_price))
                        + "\n"
                        + "BB low "
                        + str(number_for_human(bb_low))[:9]
                        + "\n"
                        + "Timeframe "
                        + str(buy_indicators_timeframe)
                        + "\n"
                        + "BUY"
                    )
                    signal = {
                        "pair": coin_pair_for_get_bars,
                        "price": coin_price,
                        "bb_low": bb_low,
                        "signal": "BUY",
                    }

                    if get_config()["ignore_buy_signal_enable"] == "YES":

                        if get_config()["ignore_buy_signal_type"] == "time":
                            return ingnore_signal_time(
                                signal, int(get_config()["ignore_buy_signal_time_sec"])
                            )
                            break

                        if get_config()["ignore_buy_signal_type"] == "times":
                            if (
                                ignore_buy_signal_times(
                                    signal, int(get_config()["ignore_buy_signal_times"])
                                )
                                == "OK"
                            ):
                                return signal
                                break
                    else:
                        return signal
                        break

                else:
                    if debug == "YES":
                        notificator("Awaiting for Signal ...")
                    time.sleep(api_requests_frequency)
                    continue

    except Exception as e:
        if show_error == "YES":
            notificator(str(e) + ' from get_indicators_signal')


def get_indicators_signal_sell(coin, coin_2, price_buy):
    coin_pair_for_get_bars = (
        coin + coin_2
    )  # another format(ETHBTC) then coin_pair(ETH/BTC) for ccxt

    try:
        while True:
            if sell_indicators_type == "RSI+BB":

                price_ok_tmp = (price_buy / 100) * price_buffer
                price_ok = price_buy + price_ok_tmp

                coin_price = check_coin_price(coin_pair_for_get_bars)
                bb_up = bollingerband(
                    coin_pair_for_get_bars, sell_indicators_timeframe
                )[1]
                rsi_data_now = rsi(coin_pair_for_get_bars, sell_indicators_timeframe)

                stop_loss = price_buy - (
                    (price_buy / 100) * stop_loss_percent_for_start_sell_on_sell_signal
                )

                if use_stop_loss_while_start_sell_on_sell_signal == "YES":
                    if coin_price <= stop_loss:
                        notificator("Stop loss, selling")
                        return {"signal": "SELL"}
                        break

                if (
                    coin_price > bb_up
                    and rsi_data_now > rsi_sell_level
                    and price_ok < coin_price
                ):

                    notificator(
                        "Pair "
                        + str(coin_pair_for_get_bars)
                        + "\n"
                        + "Price "
                        + str(number_for_human(coin_price))
                        + "\n"
                        + "BB up "
                        + str(number_for_human(bb_up))[:9]
                        + "\n"
                        + "RSI "
                        + str(rsi_data_now)[:9]
                        + "\n"
                        + "Timeframe "
                        + str(sell_indicators_timeframe)
                        + "\n"
                        + "SELL"
                    )
                    signal = {
                        "pair": coin_pair_for_get_bars,
                        "price": coin_price,
                        "bb_up": bb_up,
                        "rsi_data_now": rsi_data_now,
                        "signal": "SELL",
                    }

                    if get_config()["ignore_sell_signal_enable"] == "YES":

                        if get_config()["ignore_sell_signal_type"] == "time":
                            return ingnore_signal_time(
                                signal, int(get_config()["ignore_sell_signal_time_sec"])
                            )
                            break

                        if get_config()["ignore_sell_signal_type"] == "times":
                            if (
                                ignore_sell_signal_times(
                                    signal,
                                    int(get_config()["ignore_sell_signal_times"]),
                                )
                                == "OK"
                            ):
                                return signal
                                break
                    else:
                        return signal
                        break

                else:
                    if debug == "YES":
                        notificator("Awaiting for SELL Signal ...")
                    time.sleep(api_requests_frequency)
                    continue

            if sell_indicators_type == "RSI":
                price_ok_tmp = (price_buy / 100) * price_buffer
                price_ok = price_buy + price_ok_tmp

                coin_price = check_coin_price(coin_pair_for_get_bars)
                rsi_data_now = rsi(coin_pair_for_get_bars, sell_indicators_timeframe)

                stop_loss = price_buy - (
                    (price_buy / 100) * stop_loss_percent_for_start_sell_on_sell_signal
                )

                if use_stop_loss_while_start_sell_on_sell_signal == "YES":
                    if coin_price <= stop_loss:
                        notificator("Stop loss, selling")
                        return {"signal": "SELL"}
                        break

                if rsi_data_now > rsi_sell_level and price_ok < coin_price:

                    notificator(
                        "Pair "
                        + str(coin_pair_for_get_bars)
                        + "\n"
                        + "RSI "
                        + str(rsi_data_now)[:9]
                        + "\n"
                        + "Timeframe "
                        + str(sell_indicators_timeframe)
                        + "\n"
                        + "SELL"
                    )
                    signal = {
                        "pair": coin_pair_for_get_bars,
                        "price": coin_price,
                        "rsi_data_now": rsi_data_now,
                        "signal": "SELL",
                    }

                    if get_config()["ignore_sell_signal_enable"] == "YES":

                        if get_config()["ignore_sell_signal_type"] == "time":
                            return ingnore_signal_time(
                                signal, int(get_config()["ignore_sell_signal_time_sec"])
                            )
                            break

                        if get_config()["ignore_sell_signal_type"] == "times":
                            if (
                                ignore_sell_signal_times(
                                    signal,
                                    int(get_config()["ignore_sell_signal_times"]),
                                )
                                == "OK"
                            ):
                                return signal
                                break
                    else:
                        return signal
                        break

                else:
                    if debug == "YES":
                        notificator("Awaiting for SELL Signal ...")
                    time.sleep(api_requests_frequency)
                    continue

            if sell_indicators_type == "BB":
                price_ok_tmp = (price_buy / 100) * price_buffer
                price_ok = price_buy + price_ok_tmp

                coin_price = check_coin_price(coin_pair_for_get_bars)
                bb_up = bollingerband(
                    coin_pair_for_get_bars, sell_indicators_timeframe
                )[1]

                stop_loss = price_buy - (
                    (price_buy / 100) * stop_loss_percent_for_start_sell_on_sell_signal
                )

                if use_stop_loss_while_start_sell_on_sell_signal == "YES":
                    if coin_price <= stop_loss:
                        notificator("Stop loss, selling")
                        return {"signal": "SELL"}
                        break

                if coin_price > bb_up and price_ok < coin_price:

                    notificator(
                        "Pair "
                        + str(coin_pair_for_get_bars)
                        + "\n"
                        + "Price "
                        + str(number_for_human(coin_price))
                        + "\n"
                        + "BB up "
                        + str(number_for_human(bb_up))[:9]
                        + "\n"
                        + "Timeframe "
                        + str(sell_indicators_timeframe)
                        + "\n"
                        + "SELL"
                    )
                    signal = {
                        "pair": coin_pair_for_get_bars,
                        "price": coin_price,
                        "bb_up": bb_up,
                        "signal": "SELL",
                    }

                    if get_config()["ignore_sell_signal_enable"] == "YES":

                        if get_config()["ignore_sell_signal_type"] == "time":
                            return ingnore_signal_time(
                                signal, int(get_config()["ignore_sell_signal_time_sec"])
                            )
                            break

                        if get_config()["ignore_sell_signal_type"] == "times":
                            if (
                                ignore_sell_signal_times(
                                    signal,
                                    int(get_config()["ignore_sell_signal_times"]),
                                )
                                == "OK"
                            ):
                                return signal
                                break
                    else:
                        return signal
                        break

                else:
                    if debug == "YES":
                        notificator("Awaiting for SELL Signal ...")
                    time.sleep(api_requests_frequency)
                    continue

    except Exception as e:
        if show_error == "YES":
            notificator(str(e) + ' from get_indicators_signal_sell')

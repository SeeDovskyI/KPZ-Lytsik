import pandas as pd
import ta
from binance import Client
from dataclasses import dataclass
from typing import List
from random import uniform


@dataclass
class Signal:
    time: pd.Timestamp
    asset: str
    quantity: float
    side: str
    entry: float
    take_profit: float
    stop_loss: float
    result: float
    closed_by: str


def perform_backtesting(k_lines: pd.DataFrame):
    cci_long, cci_short = uniform(-300, 300), uniform(-300, 300)
    adx_cond = uniform(0, 100)
    take_prof_short, take_prof_long = uniform(0.005, 0.025), uniform(0.005, 0.025)
    stop_loss_short, stop_loss_long = uniform(0.005, 0.025), uniform(0.005, 0.025)
    print(
        f"{cci_long=} {cci_short=} {adx_cond=} {take_prof_long=} {take_prof_short=} {stop_loss_long=} {stop_loss_short=}")
    signals = create_signals(k_lines, cci_long, cci_short, adx_cond,
                             take_prof_long, take_prof_short, stop_loss_long,
                             stop_loss_short)
    results = []
    for signal in signals:
        start_index = k_lines[k_lines['time'] == signal.time].index[0]

        data_slice = k_lines.iloc[start_index:]

        for candle_id in range(len(data_slice)):

            if (signal.side == "sell" and data_slice.iloc[candle_id]["low"] <= signal.take_profit) or (
                    signal.side == "buy" and data_slice.iloc[candle_id]["high"] >= signal.take_profit):
                signal.result = signal.take_profit - signal.entry if signal.side == 'buy' else (
                        signal.entry - signal.take_profit)
            elif (signal.side == "sell" and data_slice.iloc[candle_id]["high"] >= signal.stop_loss) or (
                    signal.side == "buy" and data_slice.iloc[candle_id]["low"] <= signal.stop_loss):
                signal.result = signal.stop_loss - signal.entry if signal.side == 'buy' else (
                        signal.entry - signal.stop_loss)

            if signal.result is not None:
                signal.closed_by = "TP" if signal.result > 0 else "SL"
                results.append(signal)
                break
    return results


def calculate_pnl(trade_list: List[Signal]):
    total_pnl = 0
    for trade in trade_list:
        total_pnl += trade.result
    return total_pnl


def calculate_statistics(trade_list: List[Signal]):
    print(f"{calculate_pnl(trade_list)=}")
    print(f"{profit_factor(trade_list)=}")


def profit_factor(trade_list: List[Signal]):
    total_loss = 0
    total_profit = 0
    for trade in trade_list:
        if trade.result > 0:
            total_profit += trade.result
        else:
            total_loss += trade.result
    if total_loss == 0 or total_profit == 0:
        return 1
    return total_profit / abs(total_loss)


# Здесь вы должны вызвать функцию perform_backtesting и напечатать результаты


def create_signals(k_lines, cci_long, cci_short, adx_cond,
                   take_prof_long, take_prof_short, stop_loss_long, stop_loss_short):
    signals = []
    for i in range(len(k_lines)):
        current_price = k_lines.iloc[i]['close']
        if k_lines.iloc[i]['cci'] < cci_short and k_lines.iloc[i]['adx'] > adx_cond:
            signal = 'sell'
        elif k_lines.iloc[i]['cci'] > cci_long and k_lines.iloc[i]['adx'] > adx_cond:
            signal = 'buy'
        else:
            continue  # Пропускаем создание сигналов без активных условий

        if signal == "buy":
            stop_loss_price = round((1 - stop_loss_long) * current_price, 1)
            take_profit_price = round((1 + take_prof_long) * current_price, 1)
        elif signal == "sell":
            stop_loss_price = round((1 + stop_loss_short) * current_price, 1)
            take_profit_price = round((1 - take_prof_short) * current_price, 1)

        signals.append(Signal(
            k_lines.iloc[i]['time'],
            'BTCUSDT',
            100,
            signal,
            current_price,
            take_profit_price,
            stop_loss_price,
            None, None
        ))

    return signals
client = Client()
k_lines = client.get_historical_klines(
    symbol="BTCUSDT",
    interval=Client.KLINE_INTERVAL_1MINUTE,
    start_str="1 week ago UTC",
    end_str="now UTC"
)

# Создание DataFrame
k_lines = pd.DataFrame(k_lines,
                       columns=['time', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'quote_asset_volume',
                                'number_of_trades', 'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume',
                                'ignore'])
k_lines['time'] = pd.to_datetime(k_lines['time'], unit='ms')
k_lines['close'] = k_lines['close'].astype(float)
k_lines['high'] = k_lines['high'].astype(float)
k_lines['low'] = k_lines['low'].astype(float)
k_lines['open'] = k_lines['open'].astype(float)

k_lines['adx'] = ta.trend.ADXIndicator(k_lines['high'], k_lines['low'], k_lines['close']).adx()
k_lines['cci'] = ta.trend.CCIIndicator(k_lines['high'], k_lines['low'], k_lines['close']).cci()

for i in range(10):
    results=perform_backtesting(k_lines)
# for result in results:
#     print(f"Time: {result.time}, Asset: {result.asset}, Quantity: {result.quantity}, Side: {result.side}, "
#           f"Entry: {result.entry}, Take Profit: {result.take_profit}, Stop Loss: {result.stop_loss}, Result: {result.result}, Closed_by: {result.closed_by}")
    calculate_statistics(results)
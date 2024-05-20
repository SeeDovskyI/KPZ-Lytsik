import pandas as pd
import ta
from binance import Client
from dataclasses import dataclass
from typing import List


@dataclass
class Signal:
    time: pd.Timestamp
    asset: str
    quantity: float
    side: str
    entry: float
    take_profit: float
    stop_loss: float
    result: float = None
    closed_by: str = None


def perform_backtesting(k_lines: pd.DataFrame):
    signals = create_signals(k_lines)
    results = []

    # Creating index on time for quick lookup
    time_index = pd.DatetimeIndex(k_lines['time'])
    
    for signal in signals:
        start_index = time_index.get_loc(signal.time)

        data_slice = k_lines.iloc[start_index:]

        for candle_id, row in data_slice.iterrows():
            high, low = row['high'], row['low']
            if (signal.side == "sell" and low <= signal.take_profit) or (
                    signal.side == "buy" and high >= signal.take_profit):
                signal.result = signal.take_profit - signal.entry if signal.side == 'buy' else (
                        signal.entry - signal.take_profit)
                signal.closed_by = "TP"
            elif (signal.side == "sell" and high >= signal.stop_loss) or (
                    signal.side == "buy" and low <= signal.stop_loss):
                signal.result = signal.stop_loss - signal.entry if signal.side == 'buy' else (
                        signal.entry - signal.stop_loss)
                signal.closed_by = "SL"

            if signal.result is not None:
                results.append(signal)
                break
    return results


def calculate_pnl(trade_list: List[Signal]):
    return sum(trade.result for trade in trade_list)


def profit_factor(trade_list: List[Signal]):
    total_profit = sum(trade.result for trade in trade_list if trade.result > 0)
    total_loss = sum(trade.result for trade in trade_list if trade.result < 0)
    return total_profit / -total_loss if total_loss != 0 else float('inf')


def calculate_statistics(trade_list: List[Signal]):
    print(f"Total P&L: {calculate_pnl(trade_list)}")
    print(f"Profit Factor: {profit_factor(trade_list)}")


def create_signals(k_lines):
    signals = []
    for i, row in k_lines.iterrows():
        current_price = row['close']
        if row['cci'] < -100 and row['adx'] > 25:
            side = 'sell'
        elif row['cci'] > 100 and row['adx'] > 25:
            side = 'buy'
        else:
            continue  # Skip if conditions are not met

        sl_multiplier = 0.99 if side == "buy" else 1.01
        tp_multiplier = 1.015 if side == "buy" else 0.985

        signals.append(Signal(
            time=row['time'],
            asset='BTCUSDT',
            quantity=100,
            side=side,
            entry=current_price,
            take_profit=round(tp_multiplier * current_price, 1),
            stop_loss=round(sl_multiplier * current_price, 1)
        ))

    return signals


def main():
    client = Client()
    k_lines = client.get_historical_klines(
        symbol="BTCUSDT",
        interval=Client.KLINE_INTERVAL_1MINUTE,
        start_str="1 week ago UTC",
        end_str="now UTC"
    )

    # Setup DataFrame
    k_lines = pd.DataFrame(k_lines, columns=[
        'time', 'open', 'high', 'low', 'close', 'volume',
        'close_time', 'quote_asset_volume', 'number_of_trades',
        'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'])

    # Data Type Conversions
    k_lines['time'] = pd.to_datetime(k_lines['time'], unit='ms')
    for col in ['open', 'high', 'low', 'close']:
        k_lines[col] = pd.to_numeric(k_lines[col], errors='coerce')

    # Adding Technical Indicators
    adx_indicator = ta.trend.ADXIndicator(high=k_lines['high'], low=k_lines['low'], close=k_lines['close'], window=14, fillna=True)
    k_lines['adx'] = adx_indicator.adx()
    cci_indicator = ta.trend.CCIIndicator(high=k_lines['high'], low=k_lines['low'], close=k_lines['close'], window=20, constant=0.015)
    k_lines['cci'] = cci_indicator.cci()

    # Perform Backtesting
    results = perform_backtesting(k_lines)
    for result in results:
        print(f"Time: {result.time}, Asset: {result.asset}, Quantity: {result.quantity}, Side: {result.side}, "
              f"Entry: {result.entry}, Take Profit: {result.take_profit}, Stop Loss: {result.stop_loss}, Result: {result.result}, Closed by: {result.closed_by}")
    calculate_statistics(results)

if __name__ == "__main__":
    main()

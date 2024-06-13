import pandas as pd
import ta
from binance.client import Client
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

    for signal in signals:
        start_index = k_lines[k_lines['time'] == signal.time].index[0]
        data_slice = k_lines.iloc[start_index:]

        for _, candle in data_slice.iterrows():
            if signal.side == "buy":
                if candle['high'] >= signal.take_profit:
                    signal.result = signal.take_profit - signal.entry
                    signal.closed_by = "TP"
                elif candle['low'] <= signal.stop_loss:
                    signal.result = signal.stop_loss - signal.entry
                    signal.closed_by = "SL"
            elif signal.side == "sell":
                if candle['low'] <= signal.take_profit:
                    signal.result = signal.entry - signal.take_profit
                    signal.closed_by = "TP"
                elif candle['high'] >= signal.stop_loss:
                    signal.result = signal.entry - signal.stop_loss
                    signal.closed_by = "SL"

            if signal.result is not None:
                results.append(signal)
                break

    return results

def calculate_pnl(trade_list: List[Signal]):
    return sum(trade.result for trade in trade_list)

def calculate_statistics(trade_list: List[Signal]):
    total_trades = len(trade_list)
    win_trades = sum(1 for trade in trade_list if trade.result > 0)
    win_rate = win_trades / total_trades if total_trades > 0 else 0
    profit_factor_val = profit_factor(trade_list)
    total_pnl = calculate_pnl(trade_list)

    print(f"Total PNL: {total_pnl}")
    print(f"Win Rate: {win_rate * 100:.2f}%")
    print(f"Profit Factor: {profit_factor_val:.2f}")

    if total_pnl > 0.5 and win_rate > 0.4 and profit_factor_val > 1.3:
        print("Strategy meets profitability criteria")
    else:
        print("Strategy does not meet profitability criteria")

def profit_factor(trade_list: List[Signal]):
    total_profit = sum(trade.result for trade in trade_list if trade.result > 0)
    total_loss = abs(sum(trade.result for trade in trade_list if trade.result < 0))
    return total_profit / total_loss if total_loss > 0 else float('inf')

def create_signals(k_lines):
    signals = []

    for _, row in k_lines.iterrows():
        current_price = row['close']
        signal = None

        if (row['ema'] > row['vwma'] and row['sma'] > row['ema'] and row['rsi'] < 30 and row['adx'] > 20):
            signal = 'buy'
        elif (row['ema'] < row['vwma'] and row['sma'] < row['ema'] and row['rsi'] > 70 and row['adx'] > 20):
            signal = 'sell'

        if signal:
            stop_loss_price = round(current_price * (0.9925 if signal == 'buy' else 1.0075), 2)
            take_profit_price = round(current_price * (1.0215 if signal == 'buy' else 0.9785), 2)

            signals.append(Signal(
                row['time'],
                row['symbol'],
                100,
                signal,
                current_price,
                take_profit_price,
                stop_loss_price
            ))

    return signals

# Initialization of the Binance Client
client = Client(api_key='BINANCE_API_KEY', api_secret='BINANCE_API_SECRET')

# List of symbols to backtest
symbols = ["BTCUSDT", "ETHUSDT", "ETHBTC", "BNBUSDT"]

# Perform backtesting for each symbol
for symbol in symbols:
    k_lines = client.get_historical_klines(
        symbol=symbol,
        interval=Client.KLINE_INTERVAL_1MINUTE,
        start_str="2 years ago UTC",
        end_str="now UTC"
    )

    # Creating DataFrame
    k_lines = pd.DataFrame(k_lines, columns=['time', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'quote_asset_volume', 'number_of_trades', 'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'])
    k_lines['time'] = pd.to_datetime(k_lines['time'], unit='ms')
    k_lines['close'] = k_lines['close'].astype(float)
    k_lines['high'] = k_lines['high'].astype(float)
    k_lines['low'] = k_lines['low'].astype(float)
    k_lines['open'] = k_lines['open'].astype(float)
    k_lines['symbol'] = symbol

    # Add TA indicators
    k_lines['ema'] = ta.trend.EMAIndicator(k_lines['close'], window=12).ema_indicator()
    k_lines['sma'] = ta.trend.SMAIndicator(k_lines['close'], window=40).sma_indicator()
    k_lines['vwma'] = ta.volume.VolumeWeightedAveragePrice(k_lines['high'], k_lines['low'], k_lines['close'], k_lines['volume'], window=12).volume_weighted_average_price()
    k_lines['rsi'] = ta.momentum.RSIIndicator(k_lines['close'], window=40).rsi()
    k_lines['adx'] = ta.trend.ADXIndicator(k_lines['high'], k_lines['low'], k_lines['close'], window=40).adx()

    # Perform backtesting
    results = perform_backtesting(k_lines)

    # Display results
    print(f"\nResults for {symbol}:")
    for result in results:
        print(f"Time: {result.time}, Asset: {result.asset}, Quantity: {result.quantity}, Side: {result.side}, Entry: {result.entry}, Take Profit: {result.take_profit}, Stop Loss: {result.stop_loss}, Result: {result.result}, Closed_by: {result.closed_by}")

    # Calculate and display statistics
    calculate_statistics(results)

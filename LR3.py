import pandas as pd
import ta
import matplotlib.pyplot as plt
from binance.client import Client
from matplotlib.dates import DateFormatter

def fetch_binance_data(symbol, interval, start_time, end_time):
    client = Client()
    k_lines = client.get_historical_klines(
        symbol=symbol,
        interval=interval,
        start_str=start_time,
        end_str=end_time
    )
    return k_lines

def visualize_data(k_lines):
    k_lines_df = pd.DataFrame(k_lines, columns=['time', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'quote_asset_volume', 'number_of_trades', 'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'])
    k_lines_df['time'] = pd.to_datetime(k_lines_df['time'], unit='ms')
    k_lines_df[['close', 'high', 'low', 'open']] = k_lines_df[['close', 'high', 'low', 'open']].astype(float)

    # Indicator calculation
    k_lines_df['RSI'] = ta.momentum.RSIIndicator(k_lines_df['close']).rsi()
    k_lines_df['CCI'] = ta.trend.CCIIndicator(k_lines_df['high'], k_lines_df['low'], k_lines_df['close']).cci()
    k_lines_df['MACD'] = ta.trend.MACD(k_lines_df['close']).macd()
    k_lines_df['ATR'] = ta.volatility.AverageTrueRange(k_lines_df['high'], k_lines_df['low'], k_lines_df['close']).average_true_range()
    k_lines_df['ADX'] = ta.trend.ADXIndicator(k_lines_df['high'], k_lines_df['low'], k_lines_df['close']).adx()

    # Creating signal columns
    for indicator in ['RSI', 'CCI', 'MACD', 'ATR', 'ADX']:
        k_lines_df[f'{indicator}_buy_signal'] = (k_lines_df[indicator] < 30) & (k_lines_df[indicator].shift() >= 30)
        k_lines_df[f'{indicator}_sell_signal'] = (k_lines_df[indicator] > 70) & (k_lines_df[indicator].shift() <= 70)

    # Visualization of closing prices and indicators with signals
    fig, axs = plt.subplots(6, 1, figsize=(14, 10), sharex=True)

    axs[0].plot(k_lines_df['time'], k_lines_df['close'], label='Close Price', color='purple')
    axs[0].set_title('Close Price')
    axs[0].legend()

    for i, indicator in enumerate(['RSI', 'MACD', 'ATR', 'ADX', 'CCI']):
        axs[i+1].plot(k_lines_df['time'], k_lines_df[indicator], label=indicator, color='purple')
        axs[i+1].scatter(k_lines_df.loc[k_lines_df[f'{indicator}_buy_signal'], 'time'], k_lines_df.loc[k_lines_df[f'{indicator}_buy_signal'], indicator], marker='^', color='green', label='Buy Signal')
        axs[i+1].scatter(k_lines_df.loc[k_lines_df[f'{indicator}_sell_signal'], 'time'], k_lines_df.loc[k_lines_df[f'{indicator}_sell_signal'], indicator], marker='v', color='red', label='Sell Signal')
        axs[i+1].set_title(indicator)
        axs[i+1].legend()

    # Format x-axis dates
    date_form = DateFormatter("%m-%d %H:%M")
    for ax in axs:
        ax.xaxis.set_major_formatter(date_form)

    plt.tight_layout()
    plt.show()

# Loading data
symbol = "BTCUSDT"
interval = Client.KLINE_INTERVAL_1MINUTE
start_time = "1 day ago UTC"
end_time = "now UTC"
k_lines_data = fetch_binance_data(symbol, interval, start_time, end_time)

# Visualize data
visualize_data(k_lines_data)

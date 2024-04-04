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

def calculate_rsi(df, periods):
    for period in periods:
        rsi_indicator = ta.momentum.RSIIndicator(df['close'], window=period)
        df[f'RSI_{period}'] = rsi_indicator.rsi()
    return df

def visualize_data(df, periods):
    plt.figure(figsize=(14, 10))
    plt.subplot(len(periods) + 1, 1, 1)
    plt.plot(df['time'], df['close'], label='Close Price')
    plt.title('Close Price')
    plt.ylabel('Price')

    for i, period in enumerate(periods):
        plt.subplot(len(periods) + 1, 1, i + 2)
        plt.plot(df['time'], df[f'RSI_{period}'], label=f'RSI_{period}', color='purple')
        plt.title(f'RSI_{period}')
        plt.ylabel('RSI')
        plt.legend()

    # Format x-axis dates
    date_form = DateFormatter("%m-%d %H:%M")
    plt.gca().xaxis.set_major_formatter(date_form)

    plt.tight_layout()
    plt.show()

# Loading data
symbol = "BTCUSDT"
interval = Client.KLINE_INTERVAL_1MINUTE
start_time = "1 day ago UTC"
end_time = "now UTC"
k_lines_data = fetch_binance_data(symbol, interval, start_time, end_time)

# Creating DataFrame
k_lines_df = pd.DataFrame(k_lines_data, columns=['time', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'quote_asset_volume', 'number_of_trades', 'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'])
k_lines_df['time'] = pd.to_datetime(k_lines_df['time'], unit='ms')
k_lines_df[['close', 'high', 'low', 'open']] = k_lines_df[['close', 'high', 'low', 'open']].astype(float)

# Calculation of indicators
periods = [14, 27, 100]
k_lines_df = calculate_rsi(k_lines_df, periods)

# Visualization
visualize_data(k_lines_df, periods)

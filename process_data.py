import yfinance as yf
import pandas as pd


def fetch_stock_data(symbol, start_date, end_date):
    """
    Fetch stock data for a given symbol within a date range.
    :param symbol: Stock ticker symbol (e.g., 'AAPL' for Apple).
    :param start_date: Start date for historical data (e.g., '2020-01-01').
    :param end_date: End date for historical data (e.g., '2025-01-01').
    :return: DataFrame with stock data.
    """
    stock_data = yf.download(symbol, start=start_date, end=end_date)
    return stock_data


def process_data(stock_data):
    """
    Processes stock data by handling missing values and creating new features.
    :param stock_data: DataFrame containing stock data.
    :return: Processed DataFrame with new features.
    """
    # Drop missing values
    stock_data = stock_data.dropna()

    # Create moving averages (50 and 200 days)
    stock_data['SMA_50'] = stock_data['Close'].rolling(window=50).mean()
    stock_data['SMA_200'] = stock_data['Close'].rolling(window=200).mean()

    # Create price change percentage
    stock_data['price_change_pct'] = stock_data['Close'].pct_change()

    # Drop the first row due to NaN from pct_change
    stock_data = stock_data.dropna()

    return stock_data


# Example usage
if __name__ == "__main__":
    # Fetch stock data for AAPL between 2020 and 2025
    stock_data = fetch_stock_data('AAPL', '2020-01-01', '2025-01-01')

    # Process the fetched data
    processed_data = process_data(stock_data)
    print(processed_data.head())

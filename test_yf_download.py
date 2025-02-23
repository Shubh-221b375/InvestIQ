import yfinance as yf

# Fetch stock data for AAPL (Apple Inc.) from Jan 1, 2020 to Jan 1, 2025
stock_data = yf.download('AAPL', start='2020-01-01', end='2025-01-01')

# Print the first few rows to ensure data is fetched properly
print(stock_data.head())

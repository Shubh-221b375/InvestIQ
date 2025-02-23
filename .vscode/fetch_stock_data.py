import yfinance as yf

# Example: Fetch historical stock data for Tesla (TSLA)
stock = yf.Ticker("TSLA")
data = stock.history(period="1y")

# Display first few rows
print(data.head())

# Save data for analysis
data.to_csv("tsla_stock_data.csv")

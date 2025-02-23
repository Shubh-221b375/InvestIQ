import yfinance as yf
import pandas as pd
from sklearn.preprocessing import StandardScaler
import joblib

# Load the trained model
model = joblib.load('stock_price_model.pkl')

# Function to fetch and preprocess real-time stock data
def fetch_real_time_data(stock_symbol):
    # Fetch real-time data for the stock symbol entered by the user
    stock_data = yf.download(stock_symbol, period="5d", interval="1d")
    
    # Flatten the columns (remove the MultiIndex)
    stock_data.columns = stock_data.columns.get_level_values(0)
    
    # Debugging: Print the structure of the fetched data
    print(f"Fetched data for {stock_symbol}:")
    print(stock_data)
    
    # Ensure the required columns exist
    required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
    missing_columns = [col for col in required_columns if col not in stock_data.columns]
    
    if missing_columns:
        print(f"Missing columns: {missing_columns}")
        return None
    
    # Retain only relevant columns
    stock_data = stock_data[required_columns]
    
    # Debugging: Check if any rows are missing
    if stock_data.empty:
        print(f"No data fetched for stock symbol {stock_symbol}. Please check the symbol or try again later.")
        return None
    
    # Preprocess the data (same steps as used during training)
    stock_data['Price Change'] = stock_data['Close'] - stock_data['Open']
    stock_data['Price Diff'] = stock_data['Close'].diff()
    
    # Only calculate the 7-day MA if there's enough data
    if len(stock_data) >= 7:
        stock_data['7-day MA'] = stock_data['Close'].rolling(window=7).mean()
    else:
        stock_data['7-day MA'] = stock_data['Close'].rolling(window=3).mean()  # Or use a smaller window
    
    # Drop rows with NaN values created by diff() or moving averages
    stock_data.dropna(inplace=True)
    
    # Debugging: Check the processed data
    print("Processed data for prediction:")
    print(stock_data)
    
    # Select the features used for prediction
    X_real_time = stock_data[['Open', 'High', 'Low', 'Volume', 'Price Change', '7-day MA']]
    
    return X_real_time

# Example: Fetch real-time data and predict
stock_symbol = 'GOOG'  # You can replace this with any stock symbol
X_real_time = fetch_real_time_data(stock_symbol)

# If no data is returned, exit the script
if X_real_time is None or X_real_time.empty:
    print("No data available to make predictions.")
    exit()

# Print data before scaling to confirm
print("Preprocessed data for prediction:")
print(X_real_time)

# Scale the real-time data using the same scaler used during training
scaler = StandardScaler()
X_real_time_scaled = scaler.fit_transform(X_real_time)

# Make prediction
prediction = model.predict(X_real_time_scaled)
print("Predicted action (1 = Buy, 0 = Sell):", prediction[-1])  # Show prediction for the latest data

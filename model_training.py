import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score
import joblib

# Load the dataset
data = pd.read_csv("final_processed_data.csv")  # Replace with the correct file path

# Check the first few rows of the dataset to ensure correct columns
print(data.head())

# Preprocess the data
# Assuming your data has columns 'Date', 'Open', 'Close', 'High', 'Low', and 'Volume'
# If the column names are different, change them here

data['Date'] = pd.to_datetime(data['Date'])
data.set_index('Date', inplace=True)

# Feature engineering (Add more features as necessary)
data['Price Change'] = data['Close'] - data['Open']
data['Price Diff'] = data['Close'].diff()

# Example: Adding a 7-day moving average as a feature
data['7-day MA'] = data['Close'].rolling(window=7).mean()

# Drop rows with NaN values created due to the diff() or moving average calculations
data.dropna(inplace=True)

# Create the target variable based on price movement (1 = Buy, 0 = Sell)
data['Target'] = np.where(data['Price Diff'] > 0, 1, 0)

# Select features and target
X = data[['Open', 'High', 'Low', 'Volume', 'Price Change', '7-day MA']]  # Add more features if needed
y = data['Target']

# Train-test split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Feature scaling
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# Model: Logistic Regression (feel free to change this to another model like DecisionTreeClassifier, etc.)
model = LogisticRegression()
model.fit(X_train_scaled, y_train)

# Predictions
y_pred = model.predict(X_test_scaled)

# Evaluate the model
accuracy = accuracy_score(y_test, y_pred)
print(f"Accuracy: {accuracy * 100:.2f}%")

# Save the trained model to a file
joblib.dump(model, 'stock_price_model.pkl')

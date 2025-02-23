import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler

# Load the dataset
df = pd.read_csv("AAPL_stock_data.csv")

# Print first few rows to inspect the dataset
print("🔍 Initial Data Preview:")
print(df.head())

# Print column data types
print("\n🛠 Column Data Types:")
print(df.dtypes)

# Drop non-numeric columns (like stock symbols, dates)
df = df.select_dtypes(include=[np.number])

# Force numeric conversion to remove any hidden text data
df = df.apply(pd.to_numeric, errors='coerce')

# Check for remaining non-numeric values
if df.isnull().sum().sum() > 0:
    print("\n⚠️ Warning: Found non-numeric values. Filling them with column mean.")
    df = df.fillna(df.mean())

# Final check
print("\n✅ Processed Data Preview:")
print(df.head())

# Scale the numeric data
scaler = StandardScaler()
scaled_data = scaler.fit_transform(df)

# Convert back to DataFrame
scaled_df = pd.DataFrame(scaled_data, columns=df.columns)

# Print the first few rows to verify
print("\n📊 Scaled Data Preview:")
print(scaled_df.head())

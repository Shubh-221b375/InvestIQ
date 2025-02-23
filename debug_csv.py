import pandas as pd

# Load the CSV file properly (skip first two rows and set column names)
file_path = "AAPL_stock_data.csv"  # Update with actual filename
column_names = ["Date", "Close", "High", "Low", "Open", "Volume"]  # Correct column names

df = pd.read_csv(file_path, skiprows=2, names=column_names)  # Read data with correct headers

# Display first few rows
print("\n🔍 Initial Data Preview (After Cleaning):\n", df.head())

# Convert columns to correct data types
df["Close"] = pd.to_numeric(df["Close"], errors="coerce")
df["High"] = pd.to_numeric(df["High"], errors="coerce")
df["Low"] = pd.to_numeric(df["Low"], errors="coerce")
df["Open"] = pd.to_numeric(df["Open"], errors="coerce")
df["Volume"] = pd.to_numeric(df["Volume"], errors="coerce")

# Save cleaned file
df.to_csv("cleaned_data.csv", index=False)
print("\n✅ Properly Cleaned Data Saved as 'cleaned_data.csv'")

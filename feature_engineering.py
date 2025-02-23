import pandas as pd
import numpy as np

# Load CSV and fix headers
df = pd.read_csv("AAPL_stock_data.csv", skiprows=1)  # Skips the incorrect header row

# Rename 'Price' column to 'Date' if necessary
df.rename(columns={"Price": "Date"}, inplace=True)

# Print updated column names
print("✅ Updated Columns:", df.columns)

# Ensure 'Date' column exists
if "Date" not in df.columns:
    raise KeyError("❌ 'Date' column is missing. Check the dataset format.")

# Convert 'Date' column to datetime
df["Date"] = pd.to_datetime(df["Date"], errors="coerce")

# Convert numerical columns
num_cols = ["Close", "High", "Low", "Open", "Volume"]
for col in num_cols:
    if col not in df.columns:
        raise KeyError(f"❌ Column '{col}' is missing in the dataset.")
    df[col] = pd.to_numeric(df[col], errors="coerce")

# Sort data by date
df.sort_values(by="Date", inplace=True)

# Fill missing values
df.fillna(method="ffill", inplace=True)
df.fillna(method="bfill", inplace=True)

# Save the cleaned data
df.to_csv("final_processed_data.csv", index=False)

print("✅ Feature Engineering Completed! Cleaned data saved as 'final_processed_data.csv'.")

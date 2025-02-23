import pandas as pd

# Load the CSV
df = pd.read_csv("AAPL_stock_data.csv")

# Print the first few rows and column names
print("📌 First 5 Rows of the CSV:\n", df.head())

print("\n📝 Column Names in CSV:")
print(df.columns)

# Check data types
print("\n🔍 Data Types of Columns:\n", df.dtypes)

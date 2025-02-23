import sqlite3

# Connect to the database
conn = sqlite3.connect("C:\\Users\\shubh\\Documents\\Stock-Ranking-Project\\database.db")
c = conn.cursor()

# Ask user for stock name
stock_name = input("Enter the stock symbol: ").strip().upper()

# Query the database for the stock
c.execute("SELECT * FROM portfolio WHERE stock_symbol = ?", (stock_name,))
result = c.fetchall()

if result:
    print("Stock Details:")
    for row in result:
        print(f"ID: {row[0]}, User ID: {row[1]}, Stock Symbol: {row[2]}, Quantity: {row[3]}, Price: {row[4]}")
else:
    print("No records found for this stock.")

conn.close()

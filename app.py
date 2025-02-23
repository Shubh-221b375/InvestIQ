import streamlit as st
import sqlite3
import yfinance as yf
import yahooquery as yq

# 📌 Create database connection and tables
def create_connection():
    conn = sqlite3.connect("users.db", check_same_thread=False)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE,
                    password TEXT,
                    balance REAL DEFAULT 20000,
                    account_type TEXT DEFAULT 'demo'
                )''')
    c.execute('''CREATE TABLE IF NOT EXISTS portfolio (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    stock_symbol TEXT,
                    quantity INTEGER DEFAULT 0,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )''')
    conn.commit()
    return conn, c

# 📌 User authentication
def login(username, password):
    conn, c = create_connection()
    c.execute("SELECT id, balance, account_type FROM users WHERE username = ? AND password = ?", (username, password))
    user = c.fetchone()
    conn.close()
    return user

def register(username, password):
    conn, c = create_connection()
    try:
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

# 📌 Search stock
def search_stock(company_name):
    try:
        search_results = yq.search(company_name)
        if search_results and "quotes" in search_results and len(search_results["quotes"]) > 0:
            stock_symbol = search_results["quotes"][0]["symbol"]
            stock = yf.Ticker(stock_symbol)
            return stock_symbol, stock.info
        return None, None
    except Exception as e:
        return None, None

# 📌 Buy or sell stock
def trade_stock(user_id, stock_symbol, quantity, buy=True):
    conn, c = create_connection()
    c.execute("SELECT balance FROM users WHERE id = ?", (user_id,))
    balance = c.fetchone()[0]
    
    try:
        stock_price = yf.Ticker(stock_symbol).history(period="1d")["Close"][0]
    except:
        return "⚠️ Failed to retrieve stock price!"
    
    total_cost = stock_price * quantity

    if buy:
        if balance >= total_cost:
            c.execute("INSERT INTO portfolio (user_id, stock_symbol, quantity) VALUES (?, ?, ?) ON CONFLICT(stock_symbol) DO UPDATE SET quantity = quantity + ?", 
                      (user_id, stock_symbol, quantity, quantity))
            c.execute("UPDATE users SET balance = balance - ? WHERE id = ?", (total_cost, user_id))
            conn.commit()
            conn.close()
            return f"✅ Bought {quantity} of {stock_symbol} at ₹{stock_price:.2f} each!"
        else:
            return "❌ Insufficient funds!"
    else:
        c.execute("SELECT quantity FROM portfolio WHERE user_id = ? AND stock_symbol = ?", (user_id, stock_symbol))
        owned = c.fetchone()
        if owned and owned[0] >= quantity:
            c.execute("UPDATE portfolio SET quantity = quantity - ? WHERE user_id = ? AND stock_symbol = ?", 
                      (quantity, user_id, stock_symbol))
            c.execute("UPDATE users SET balance = balance + ? WHERE id = ?", (total_cost, user_id))
            conn.commit()
            conn.close()
            return f"✅ Sold {quantity} of {stock_symbol} at ₹{stock_price:.2f} each!"
        else:
            return "❌ Not enough stocks to sell!"

# 📌 Fetch user portfolio
def get_portfolio(user_id):
    conn, c = create_connection()
    c.execute("SELECT stock_symbol, quantity FROM portfolio WHERE user_id = ?", (user_id,))
    portfolio = c.fetchall()
    conn.close()
    return portfolio

# 📌 Main Streamlit app
def main():
    st.title("📊 Stock Trading Platform")
    menu = ["Login", "Register"]
    choice = st.sidebar.selectbox("Menu", menu)
    
    if choice == "Login":
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            user = login(username, password)
            if user:
                st.session_state.user = user
                st.rerun()
            else:
                st.error("❌ Invalid credentials")
    
    elif choice == "Register":
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Register"):
            if register(username, password):
                st.success("✅ Registration successful! Please log in.")
                st.session_state.user = login(username, password)
                st.rerun()
            else:
                st.error("❌ Username already exists.")

    if "user" in st.session_state:
        user = st.session_state.user
        st.sidebar.title(f"💰 Balance: ₹{user[1]:,.2f}")
        option = st.sidebar.radio("📌 Choose an option", ["Stock Search", "Trade Stocks", "Portfolio"])
        
        if option == "Stock Search":
            st.subheader("🔍 Search Stock by Company Name")
            company_name = st.text_input("Enter company name:")
            if st.button("Search"):
                stock_symbol, stock_info = search_stock(company_name)
                if stock_symbol:
                    st.write(f"### {stock_info.get('longName', 'Unknown')}")
                    st.line_chart(yf.download(stock_symbol, period="1mo")["Close"])
                else:
                    st.error("❌ Stock not found!")

        elif option == "Trade Stocks":
            st.subheader("💹 Buy or Sell Stocks")
            company_name = st.text_input("Enter company name:")
            if st.button("Find Stock"):
                stock_symbol, _ = search_stock(company_name)
                if stock_symbol:
                    quantity = st.number_input("Enter quantity to trade", min_value=1)
                    if st.button("Buy Stock"):
                        st.success(trade_stock(user[0], stock_symbol, quantity, buy=True))
                    if st.button("Sell Stock"):
                        st.success(trade_stock(user[0], stock_symbol, quantity, buy=False))
                else:
                    st.error("❌ Stock not found!")

        elif option == "Portfolio":
            st.subheader("📈 Your Portfolio")
            portfolio = get_portfolio(user[0])
            if portfolio:
                for stock in portfolio:
                    st.write(f"🔹 **Stock:** {stock[0]}, **Quantity:** {stock[1]}")
            else:
                st.write("No stocks in portfolio.")

if __name__ == "__main__":
    main()

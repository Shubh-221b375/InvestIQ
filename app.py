import streamlit as st
import sqlite3
import yfinance as yf
import yahooquery as yq
import plotly.graph_objects as go
from datetime import datetime

# 📌 Create database connection and tables with new schema
def create_connection():
    conn = sqlite3.connect("users.db", check_same_thread=False)
    c = conn.cursor()
    
    # Create tables with updated schema
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
                    average_cost REAL,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    stock_symbol TEXT,
                    quantity INTEGER,
                    price REAL,
                    type TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    profit_loss REAL,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )''')
    
    # Check if the `average_cost` column exists in the `portfolio` table
    c.execute("PRAGMA table_info(portfolio)")
    columns = [column[1] for column in c.fetchall()]
    if "average_cost" not in columns:
        c.execute("ALTER TABLE portfolio ADD COLUMN average_cost REAL;")
    
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

# 📌 Enhanced stock search with current price
def search_stock(company_name):
    try:
        search_results = yq.search(company_name)
        if search_results and "quotes" in search_results and len(search_results["quotes"]) > 0:
            stock_symbol = search_results["quotes"][0]["symbol"]
            stock = yf.Ticker(stock_symbol)
            current_price = stock.history(period="1d")["Close"].iloc[-1]
            return stock_symbol, stock.info, current_price
        else:
            st.warning(f"No results found for '{company_name}'.")
            return None, None, None
    except Exception as e:
        st.error(f"An error occurred while searching for the stock: {e}")
        return None, None, None

# 📌 Enhanced trade function with average cost and profit tracking
def trade_stock(user_id, stock_symbol, quantity, buy=True):
    conn, c = create_connection()
    c.execute("SELECT balance FROM users WHERE id = ?", (user_id,))
    balance = c.fetchone()[0]
    
    try:
        stock_price = yf.Ticker(stock_symbol).history(period="1d")["Close"].iloc[-1]
    except:
        return "⚠️ Failed to retrieve stock price!"
    
    total_cost = stock_price * quantity

    if buy:
        if balance >= total_cost:
            # Check existing holdings
            c.execute("SELECT quantity, average_cost FROM portfolio WHERE user_id = ? AND stock_symbol = ?", 
                     (user_id, stock_symbol))
            existing = c.fetchone()
            
            if existing:
                old_qty, old_avg = existing
                new_qty = old_qty + quantity
                new_avg = ((old_avg * old_qty) + (stock_price * quantity)) / new_qty
                c.execute("UPDATE portfolio SET quantity = ?, average_cost = ? WHERE user_id = ? AND stock_symbol = ?",
                         (new_qty, new_avg, user_id, stock_symbol))
            else:
                c.execute("INSERT INTO portfolio (user_id, stock_symbol, quantity, average_cost) VALUES (?, ?, ?, ?)",
                         (user_id, stock_symbol, quantity, stock_price))
            
            # Update balance
            c.execute("UPDATE users SET balance = balance - ? WHERE id = ?", (total_cost, user_id))
            
            # Record transaction
            c.execute("INSERT INTO orders (user_id, stock_symbol, quantity, price, type, profit_loss) VALUES (?, ?, ?, ?, ?, ?)",
                     (user_id, stock_symbol, quantity, stock_price, 'buy', None))
            
            conn.commit()
            conn.close()
            return f"✅ Order Successful! Bought {quantity} of {stock_symbol} at ₹{stock_price:.2f} each."
        else:
            return "❌ Insufficient funds!"
    else:
        # Check existing holdings
        c.execute("SELECT quantity, average_cost FROM portfolio WHERE user_id = ? AND stock_symbol = ?", 
                 (user_id, stock_symbol))
        existing = c.fetchone()
        
        if existing and existing[0] >= quantity:
            old_qty, old_avg = existing
            new_qty = old_qty - quantity
            profit_loss = (stock_price - old_avg) * quantity
            
            if new_qty > 0:
                c.execute("UPDATE portfolio SET quantity = ? WHERE user_id = ? AND stock_symbol = ?",
                         (new_qty, user_id, stock_symbol))
            else:
                c.execute("DELETE FROM portfolio WHERE user_id = ? AND stock_symbol = ?",
                         (user_id, stock_symbol))
            
            # Update balance
            c.execute("UPDATE users SET balance = balance + ? WHERE id = ?", 
                     (stock_price * quantity, user_id))
            
            # Record transaction
            c.execute("INSERT INTO orders (user_id, stock_symbol, quantity, price, type, profit_loss) VALUES (?, ?, ?, ?, ?, ?)",
                     (user_id, stock_symbol, quantity, stock_price, 'sell', profit_loss))
            
            conn.commit()
            conn.close()
            return f"✅ Order Successful! Sold {quantity} of {stock_symbol} at ₹{stock_price:.2f} each. P/L: ₹{profit_loss:.2f}"
        else:
            return "❌ Not enough stocks to sell!"

# 📌 Enhanced portfolio display with profit/loss
def get_portfolio(user_id):
    conn, c = create_connection()
    c.execute("SELECT stock_symbol, quantity, average_cost FROM portfolio WHERE user_id = ?", (user_id,))
    portfolio = c.fetchall()
    conn.close()
    return portfolio

# 📌 Get order history
def get_order_history(user_id):
    conn, c = create_connection()
    c.execute("SELECT stock_symbol, quantity, price, type, timestamp, profit_loss FROM orders WHERE user_id = ? ORDER BY timestamp DESC", (user_id,))
    history = c.fetchall()
    conn.close()
    return history

# 📌 Main Streamlit app with new features
def main():
    st.title("📊 Stock Trading Platform")
    
    # Page persistence in query params
    query_params = st.query_params
    default_page = query_params.get("page", ["Stock Search"])[0]
    
    if "user" not in st.session_state:
        menu = ["Login", "Register"]
        choice = st.sidebar.selectbox("Menu", menu)
        
        if choice == "Login":
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            if st.button("Login"):
                user = login(username, password)
                if user:
                    st.session_state.user = user
                    st.query_params["page"] = "Portfolio"
                    st.rerun()
                else:
                    st.error("❌ Invalid credentials")
        
        elif choice == "Register":
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            if st.button("Register"):
                if register(username, password):
                    st.success("✅ Registration successful! Please log in.")
                else:
                    st.error("❌ Username already exists.")
    
    else:
        user = st.session_state.user
        st.sidebar.title(f"💰 Balance: ₹{user[1]:,.2f}")
        
        # Navigation with persistence
        options = ["Stock Search", "Portfolio", "Order History"]
        nav_choice = st.sidebar.radio("📌 Navigation", options, index=options.index(default_page) if default_page in options else 0)
        st.query_params["page"] = nav_choice
        
        if nav_choice == "Stock Search":
            st.subheader("🔍 Search Stock")
            company_name = st.text_input("Enter company name:")
            
            if st.button("Search"):
                stock_symbol, stock_info, current_price = search_stock(company_name)
                if stock_symbol:
                    st.session_state.current_stock = {
                        "symbol": stock_symbol,
                        "info": stock_info,
                        "price": current_price
                    }
                else:
                    st.session_state.current_stock = None
            
            if "current_stock" in st.session_state and st.session_state.current_stock is not None:
                stock = st.session_state.current_stock
                if stock['info'] is not None:
                    st.write(f"### {stock['info'].get('longName', stock['symbol'])}")
                    st.write(f"**Current Price:** ₹{stock['price']:.2f}")
                    
                    # Fetch historical data
                    data = yf.download(stock['symbol'], period="1mo")
                    
                    # Debug: Display the first few rows of the data
                    st.write("**Historical Data:**")
                    st.write(data.head())
                    
                    # Check if data is valid
                    if not data.empty:
                        # Candlestick chart
                        fig = go.Figure(data=[go.Candlestick(
                            x=data.index,
                            open=data['Open'],
                            high=data['High'],
                            low=data['Low'],
                            close=data['Close']
                        )])
                        fig.update_layout(
                            title=f"{stock['symbol']} Price History",
                            xaxis_title="Date",
                            yaxis_title="Price (₹)"
                        )
                        st.plotly_chart(fig)
                    else:
                        st.error("No data available for the selected stock.")
                    
                    # Trading interface
                    quantity = st.number_input("Shares", min_value=1, key="trade_qty")
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("Buy"):
                            result = trade_stock(user[0], stock['symbol'], quantity, buy=True)
                            st.success(result)
                            st.session_state.current_stock = None
                            st.rerun()
                    with col2:
                        if st.button("Sell"):
                            result = trade_stock(user[0], stock['symbol'], quantity, buy=False)
                            st.success(result)
                            st.session_state.current_stock = None
                            st.rerun()
                else:
                    st.error("Failed to retrieve stock information. Please try again.")
            else:
                st.warning("No stock selected. Please search for a stock.")
        
        elif nav_choice == "Portfolio":
            st.subheader("📈 Your Portfolio")
            portfolio = get_portfolio(user[0])
            
            if portfolio:
                total_value = 0
                total_profit = 0
                total_loss = 0
                
                for stock in portfolio:
                    symbol, qty, avg_cost = stock
                    try:
                        current_price = yf.Ticker(symbol).history(period="1d")["Close"].iloc[-1]
                    except:
                        current_price = avg_cost
                    
                    current_value = qty * current_price
                    profit_loss = (current_price - avg_cost) * qty
                    total_value += current_value
                    
                    if profit_loss >= 0:
                        total_profit += profit_loss
                    else:
                        total_loss += abs(profit_loss)
                    
                    st.write(f"""
                    **{symbol}**  
                    Quantity: {qty}  
                    Avg Cost: ₹{avg_cost:.2f}  
                    Current Price: ₹{current_price:.2f}  
                    Current Value: ₹{current_value:.2f}  
                    Unrealized P/L: ₹{profit_loss:.2f}
                    """)
                    st.write("---")
                
                st.write(f"**Total Portfolio Value:** ₹{total_value:.2f}")  
                st.write(f"**Total Unrealized Profit:** ₹{total_profit:.2f}")  
                st.write(f"**Total Unrealized Loss:** ₹{total_loss:.2f}")
            else:
                st.write("Your portfolio is empty")
        
        elif nav_choice == "Order History":
            st.subheader("📜 Order History")
            history = get_order_history(user[0])
            
            if history:
                for order in history:
                    symbol, qty, price, otype, timestamp, pl = order
                    st.write(f"""
                    **{otype.upper()}** {qty} shares of {symbol}  
                    Price: ₹{price:.2f}  
                    Date: {datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S').strftime('%d %b %Y %H:%M')}  
                    {f"Profit/Loss: ₹{pl:.2f}" if otype == 'sell' else ''}
                    """)
                    st.write("---")
            else:
                st.write("No orders to display")

if __name__ == "__main__":
    main()

import streamlit as st
import sqlite3
import yfinance as yf
import yahooquery as yq
import pandas as pd
import numpy as np
import streamlit.components.v1 as components

# Database setup
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
                average_cost REAL,
                UNIQUE(user_id, stock_symbol)
            )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                stock_symbol TEXT,
                quantity INTEGER,
                price REAL,
                type TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                profit_loss REAL
            )''')
    
    conn.commit()
    return conn, c

# User authentication
def login(username, password):
    conn, c = create_connection()
    try:
        c.execute("SELECT id, balance FROM users WHERE username = ? AND password = ?", 
                (username, password))
        return c.fetchone()
    finally:
        conn.close()

def register(username, password):
    conn, c = create_connection()
    try:
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)", 
                (username, password))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

# Trading functions with fixed UNIQUE constraint handling
def trade_stock(user_id, stock_symbol, quantity, buy=True):
    conn, c = create_connection()
    try:
        stock_symbol = stock_symbol.upper()  # Normalize symbol case
        
        c.execute("SELECT balance FROM users WHERE id = ?", (user_id,))
        balance_row = c.fetchone()
        if not balance_row:
            return "❌ User not found"
        balance = balance_row[0]
        
        stock = yf.Ticker(stock_symbol)
        hist = stock.history(period="1d")
        if hist.empty:
            return "⚠️ Failed to get stock price"
        
        stock_price = hist["Close"].iloc[-1]
        total_cost = stock_price * quantity

        if buy:
            if balance < total_cost:
                return "❌ Insufficient funds"
            
            # Handle portfolio update with proper conflict resolution
            c.execute('''INSERT INTO portfolio (user_id, stock_symbol, quantity, average_cost)
                        VALUES (?, ?, ?, ?)
                        ON CONFLICT(user_id, stock_symbol) DO UPDATE SET
                        quantity = portfolio.quantity + excluded.quantity,
                        average_cost = ((portfolio.quantity * portfolio.average_cost) + 
                                      (excluded.quantity * excluded.average_cost)) / 
                                      (portfolio.quantity + excluded.quantity)
                     ''', (user_id, stock_symbol, quantity, stock_price))
        else:
            c.execute("SELECT quantity, average_cost FROM portfolio WHERE user_id = ? AND stock_symbol = ?",
                     (user_id, stock_symbol))
            holding = c.fetchone()
            if not holding or holding[0] < quantity:
                return "❌ Not enough shares to sell"
            
            new_quantity = holding[0] - quantity
            if new_quantity <= 0:
                c.execute("DELETE FROM portfolio WHERE user_id = ? AND stock_symbol = ?",
                         (user_id, stock_symbol))
            else:
                c.execute("UPDATE portfolio SET quantity = ? WHERE user_id = ? AND stock_symbol = ?",
                         (new_quantity, user_id, stock_symbol))

        # Update balance
        new_balance = balance - total_cost if buy else balance + total_cost
        c.execute("UPDATE users SET balance = ? WHERE id = ?", (new_balance, user_id))
        
        # Record transaction
        pl = (stock_price - holding[1]) * quantity if not buy and holding else None
        c.execute('''INSERT INTO orders (user_id, stock_symbol, quantity, price, type, profit_loss)
                    VALUES (?, ?, ?, ?, ?, ?)''',
                (user_id, stock_symbol, quantity, stock_price, 'buy' if buy else 'sell', pl))
        
        conn.commit()
        return f"✅ {'Bought' if buy else 'Sold'} {quantity} shares of {stock_symbol} @ ₹{stock_price:.2f}"
    
    except Exception as e:
        conn.rollback()
        return f"⚠️ Error: {str(e)}"
    finally:
        conn.close()

# Enhanced TradingView chart with company name search
def display_tradingview_chart(symbol, market_type):
    symbol = symbol.upper()
    if market_type == "Indian":
        if not symbol.endswith(('.NS', '.BO')):
            symbol += '.NS'
        exchange = "NSE" if symbol.endswith('.NS') else "BSE"
        clean_symbol = symbol.replace('.NS','').replace('.BO','')
    else:
        exchange = "NASDAQ"
        clean_symbol = symbol

    html = f"""
    <div style="height:95vh; width:100%;">
    <div class="tradingview-widget-container" style="height:100%; width:100%;">
      <div id="tradingview_{clean_symbol}" style="height:100%; width:100%;"></div>
      <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
      <script type="text/javascript">
      new TradingView.widget(
        {{
          "autosize": true,
          "symbol": "{exchange}:{clean_symbol}",
          "interval": "1",
          "timezone": "Asia/Kolkata",
          "theme": "dark",
          "style": "1",
          "locale": "en",
          "enable_publishing": false,
          "allow_symbol_change": true,
          "studies": ["Volume@tv-basicstudies"],
          "container_id": "tradingview_{clean_symbol}"
        }}
      );
      </script>
    </div>
    </div>
    """
    components.html(html, height=1000, scrolling=True)

# Main application
def main():
    st.title("📈 Global Trading Platform")
    
    if "user" not in st.session_state:
        auth_type = st.sidebar.radio("Menu", ["Login", "Register"])
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        
        if st.button(auth_type):
            if auth_type == "Login":
                user = login(username, password)
                if user:
                    st.session_state.user = user
                    st.rerun()
                else:
                    st.error("Invalid credentials")
            else:
                if register(username, password):
                    st.success("Registration successful! Please login")
                else:
                    st.error("Username already exists")
        return
    
    user_id, balance = st.session_state.user
    st.sidebar.title(f"Account Balance: ₹{balance:,.2f}")
    
    page = st.sidebar.radio("Navigation", [
        "Trade Stocks", 
        "Portfolio", 
        "Order History", 
        "Live Charts", 
        "Stock Analysis"
    ])

    if page == "Trade Stocks":
        st.header("Stock Trading")
        market_type = st.selectbox("Select Market Type", ["Indian", "International"], key="trade_market")
        search_term = st.text_input("Search Company Name:")
        
        if search_term:
            try:
                results = yq.search(search_term)
                if results.get('quotes'):
                    if market_type == "Indian":
                        options = [f"{q['longname']} ({q['symbol']})" 
                                 for q in results['quotes'] 
                                 if q['symbol'].endswith(('.NS', '.BO'))]
                    else:
                        options = [f"{q['longname']} ({q['symbol']})" 
                                 for q in results['quotes'] 
                                 if not q['symbol'].endswith(('.NS', '.BO'))]
                    
                    if options:
                        selected = st.selectbox("Select Company", options)
                        symbol = selected.split('(')[-1].rstrip(')')
                        
                        stock = yf.Ticker(symbol)
                        info = stock.info
                        
                        st.subheader(info.get('longName', symbol))
                        col1, col2 = st.columns(2)
                        with col1:
                            price = info.get('currentPrice', 0)
                            st.metric("Current Price", f"₹{price:.2f}")
                        with col2:
                            day_low = info.get('dayLow', 0)
                            day_high = info.get('dayHigh', 0)
                            st.metric("Day Range", f"₹{day_low:.2f} - ₹{day_high:.2f}")
                        
                        quantity = st.number_input("Shares", min_value=1, value=10)
                        total = price * quantity
                        st.write(f"Total Value: ₹{total:,.2f}")
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button(f"Buy {quantity} Shares"):
                                result = trade_stock(user_id, symbol, quantity, True)
                                # Refresh balance
                                conn, c = create_connection()
                                c.execute("SELECT balance FROM users WHERE id = ?", (user_id,))
                                st.session_state.user = (user_id, c.fetchone()[0])
                                conn.close()
                                st.success(result)
                                st.rerun()
                        with col2:
                            if st.button(f"Sell {quantity} Shares"):
                                result = trade_stock(user_id, symbol, quantity, False)
                                # Refresh balance
                                conn, c = create_connection()
                                c.execute("SELECT balance FROM users WHERE id = ?", (user_id,))
                                st.session_state.user = (user_id, c.fetchone()[0])
                                conn.close()
                                st.success(result)
                                st.rerun()
                    else:
                        st.error("No matching stocks found")
            except Exception as e:
                st.error(f"Search error: {str(e)}")

    elif page == "Portfolio":
        st.header("Your Portfolio")
        conn, c = create_connection()
        try:
            portfolio = c.execute('''SELECT stock_symbol, quantity, average_cost 
                                   FROM portfolio WHERE user_id = ?''', (user_id,)).fetchall()
            
            if portfolio:
                total_value = 0
                for symbol, qty, avg_cost in portfolio:
                    try:
                        stock = yf.Ticker(symbol)
                        hist = stock.history(period='1d')
                        if not hist.empty:
                            price = hist['Close'].iloc[-1]
                            value = qty * price
                            total_value += value
                            pl = (price - avg_cost) * qty
                            
                            st.write(f"""
                            **{symbol}**
                            - Shares: {qty}
                            - Avg Cost: ₹{avg_cost:.2f}
                            - Current Value: ₹{value:,.2f}
                            - Unrealized P/L: ₹{pl:+,.2f}
                            """)
                    except:
                        st.warning(f"Could not fetch data for {symbol}")
                st.metric("Total Portfolio Value", f"₹{total_value:,.2f}")
            else:
                st.info("Your portfolio is empty")
        finally:
            conn.close()

    elif page == "Order History":
        st.header("Order History")
        conn, c = create_connection()
        try:
            orders = c.execute('''SELECT stock_symbol, quantity, price, type, timestamp, profit_loss 
                                FROM orders WHERE user_id = ? ORDER BY timestamp DESC''', 
                             (user_id,)).fetchall()
            
            if orders:
                for symbol, qty, price, otype, ts, pl in orders:
                    st.write(f"""
                    **{otype.upper()}** {qty} shares of {symbol}
                    - Price: ₹{price:.2f}
                    - Date: {ts.split('.')[0]}
                    {f"- P/L: ₹{pl:+,.2f}" if pl else ""}
                    """)
            else:
                st.info("No orders found")
        finally:
            conn.close()

    elif page == "Live Charts":
        st.header("Live Market Charts")
        col1, col2 = st.columns([3, 1])
        
        with col1:
            market_type = st.selectbox("Select Market Type", ["Indian", "International"], key="chart_market")
            search_term = st.text_input("Search Company Name:", key="chart_search")
            symbol = None
            
            if search_term:
                try:
                    results = yq.search(search_term)
                    if results.get('quotes'):
                        if market_type == "Indian":
                            options = [f"{q['longname']} ({q['symbol']})" 
                                     for q in results['quotes'] 
                                     if q['symbol'].endswith(('.NS', '.BO'))]
                        else:
                            options = [f"{q['longname']} ({q['symbol']})" 
                                     for q in results['quotes'] 
                                     if not q['symbol'].endswith(('.NS', '.BO'))]
                        
                        if options:
                            selected = st.selectbox("Select Company", options, key="chart_select")
                            symbol = selected.split('(')[-1].rstrip(')')
                            display_tradingview_chart(symbol, market_type)
                        else:
                            st.error("No matching stocks found")
                except Exception as e:
                    st.error(f"Search error: {str(e)}")
        
        with col2:
            st.markdown("### Chart Guide")
            st.write("""
            - Search by company name (e.g., "TCS", "Apple")
            - Real-time 1-second interval updates
            - Full technical analysis toolkit
            - Drag to resize chart area
            """)

    elif page == "Stock Analysis":
        st.header("Technical Analysis")
        st.write("## Coming Soon!")
        st.write("Our team is working hard to bring you advanced technical analysis features.")
        st.image("https://via.placeholder.com/600x200?text=Feature+In+Development", use_column_width=True)

if __name__ == "__main__":
    main()

import sqlite3
import pandas as pd
from datetime import datetime

DB_NAME = "portfolio_risk.db"

def init_db():
    """Initializes database tables and data governance audit logs."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Store clean historical market data
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS historical_prices (
            ticker TEXT,
            date TEXT,
            close_price REAL,
            PRIMARY KEY (ticker, date)
        )
    ''')
    
    # Audit log for Data Governance
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS data_governance_log (
            timestamp TEXT,
            action TEXT,
            status TEXT,
            records_processed INTEGER
        )
    ''')
    conn.commit()
    conn.close()

def log_governance_event(action, status, count):
    """Logs data lineage and pipeline health for enterprise compliance."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO data_governance_log VALUES (?, ?, ?, ?)",
        (datetime.now().isoformat(), action, status, count)
    )
    conn.commit()
    conn.close()

def save_to_db(df, ticker):
    """Saves DataFrame into SQLite, gracefully ignoring duplicates to ensure data governance."""
    conn = sqlite3.connect(DB_NAME)
    df_to_save = df[['Close']].reset_index()
    df_to_save.columns = ['date', 'close_price']
    df_to_save['date'] = pd.to_datetime(df_to_save['date']).dt.strftime('%Y-%m-%d')
    df_to_save['ticker'] = ticker
    
    # Create a temporary staging table to handle the upsert (Update or Insert)
    df_to_save.to_sql('temp_staging', conn, if_exists='replace', index=False)
    
    cursor = conn.cursor()
    # SQL query that inserts new data, but ignores rows where ticker + date already exist
    cursor.execute('''
        INSERT OR IGNORE INTO historical_prices (ticker, date, close_price)
        SELECT ticker, date, close_price FROM temp_staging
    ''')
    
    # Clean up staging table
    cursor.execute('DROP TABLE temp_staging')
    
    conn.commit()
    log_governance_event(f"Ingested and checked duplicates for {ticker}", "SUCCESS", len(df_to_save))
    conn.close()

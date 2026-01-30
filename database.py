import sqlite3

def connect_db():
    return sqlite3.connect("grocery.db")

def create_table():
    conn = connect_db()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        cost_price REAL,
        sell_price REAL,
        quantity INTEGER
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS sales (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        invoice_no INTEGER,
        product_name TEXT,
        qty INTEGER,
        subtotal REAL,
        cgst REAL,
        sgst REAL,
        total REAL,
        profit REAL
    )
    """)

    conn.commit()
    conn.close()

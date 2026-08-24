import sqlite3

def init_db():
    conn = sqlite3.connect("sumer_system.db")
    cursor = conn.cursor()
    
    # جدول المشتركين
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS subscribers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            chat_id TEXT UNIQUE NOT NULL
        )
    """)
    
    # جدول الأسواق والأصول المالية الشاملة
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS markets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            category TEXT NOT NULL
        )
    """)
    
    conn.commit()
    
    # إضافة الأصول الشاملة الافتراضية
    default_markets = [
        ("BTCUSDT", "البيتكوين (Bitcoin)", "Crypto"),
        ("ETHUSDT", "الإيثيريوم (Ethereum)", "Crypto"),
        ("SOLUSDT", "سولانا (Solana)", "Crypto"),
        ("BNBUSDT", "باينانس كوين (BNB)", "Crypto"),
        ("XRPUSDT", "ريبل (XRP)", "Crypto"),
        ("XAUUSDT", "الذهب العالمي (Gold)", "Commodities"),
        ("XAGUSDT", "الفضة العالمية (Silver)", "Commodities"),
        ("AAPL", "أبل (Apple Inc.)", "Stocks"),
        ("NVDA", "إنفيديا (NVIDIA)", "Stocks"),
        ("TSLA", "تيسلا (Tesla)", "Stocks"),
        ("MSFT", "مايكروسوفت (Microsoft)", "Stocks")
    ]
    
    for symbol, name, category in default_markets:
        try:
            cursor.execute("INSERT INTO markets (symbol, name, category) VALUES (?, ?, ?)", (symbol, name, category))
        except sqlite3.IntegrityError:
            pass
            
    conn.commit()
    conn.close()

def add_subscriber(name, chat_id):
    conn = sqlite3.connect("sumer_system.db")
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO subscribers (name, chat_id) VALUES (?, ?)", (name, str(chat_id).strip()))
        conn.commit()
    except sqlite3.IntegrityError:
        pass
    finally:
        conn.close()

def get_all_subscribers():
    conn = sqlite3.connect("sumer_system.db")
    cursor = conn.cursor()
    cursor.execute("SELECT chat_id FROM subscribers")
    subscribers = [row[0] for row in cursor.fetchall()]
    conn.close()
    return subscribers

def get_all_markets():
    conn = sqlite3.connect("sumer_system.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT symbol, name, category FROM markets")
    rows = cursor.fetchall()
    conn.close()
    return [{"symbol": row["symbol"], "name": row["name"], "category": row["category"]} for row in rows]
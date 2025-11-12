import sqlite3
from datetime import datetime, timezone

DATABASE_PATH = r"D:/GIO.BOT.002/data/gio_crypto_bot.db"

def insert_test_signal():
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    now_str = datetime.utcnow().isoformat()

    cursor.execute("""
    INSERT INTO signals (symbol, direction, entry_price, tp1, tp2, tp3, stop_loss, status, timestamp)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, ("ETHUSDT", "LONG", 3400.0, 3500.0, 3600.0, 3700.0, 3300.0, "active", now_str))

    conn.commit()
    conn.close()
    print("Тестовый сигнал вставлен.")

if __name__ == "__main__":
    insert_test_signal()

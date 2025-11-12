import sqlite3

DATABASE_PATH = r"D:/GIO.BOT.002/data/gio_crypto_bot.db"

conn = sqlite3.connect(DATABASE_PATH)
cursor = conn.cursor()

cursor.execute("SELECT id, symbol, direction, entry_price, tp1, tp2, tp3, stop_loss FROM signals WHERE status='active'")
signals = cursor.fetchall()

print(f"Active signals count: {len(signals)}")
for s in signals:
    print(s)

conn.close()


# python .\check_active_signals.py

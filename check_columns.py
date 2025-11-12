import sqlite3

conn = sqlite3.connect(r"D:/GIO.BOT.002/data/gio_crypto_bot.db")
cursor = conn.cursor()

cursor.execute("PRAGMA table_info(signals)")
columns = cursor.fetchall()
conn.close()

print("Колонки в таблице signals:")
for col in columns:
    print(f"- {col[1]} ({col[2]})")

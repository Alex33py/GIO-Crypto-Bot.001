# Создай check_signal_dates.py
import sqlite3

conn = sqlite3.connect('data/gio_crypto_bot.db')
cursor = conn.cursor()

# 1. Min и Max даты
cursor.execute("SELECT MIN(timestamp), MAX(timestamp) FROM signals")
min_date, max_date = cursor.fetchone()
print(f"📅 Signal date range:")
print(f"  From: {min_date}")
print(f"  To: {max_date}")

# 2. Сигналы по дням
cursor.execute("""
    SELECT DATE(timestamp) as date, COUNT(*) as count
    FROM signals
    GROUP BY DATE(timestamp)
    ORDER BY date DESC
    LIMIT 15
""")
print(f"\n📊 Signals by date (last 15 days):")
for row in cursor.fetchall():
    print(f"  {row[0]}: {row[1]} signals")

conn.close()

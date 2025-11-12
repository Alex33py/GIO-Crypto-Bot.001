#!/usr/bin/env python3
import sqlite3
from datetime import datetime, timedelta

# Подключиться к БД
conn = sqlite3.connect('data/gio_crypto_bot.db')
cursor = conn.cursor()

# 1. Всего сигналов
cursor.execute("SELECT COUNT(*) FROM signals")
total = cursor.fetchone()[0]
print(f"✅ Total signals: {total}")

# 2. Новых за 15 минут
cursor.execute("SELECT COUNT(*) FROM signals WHERE timestamp > datetime('now', '-15 minutes')")
new_15 = cursor.fetchone()[0]
print(f"✅ New signals (last 15 min): {new_15}")

# 3. Новых за 30 минут
cursor.execute("SELECT COUNT(*) FROM signals WHERE timestamp > datetime('now', '-30 minutes')")
new_30 = cursor.fetchone()[0]
print(f"✅ New signals (last 30 min): {new_30}")

# 4. Новых за 1 час
cursor.execute("SELECT COUNT(*) FROM signals WHERE timestamp > datetime('now', '-1 hour')")
new_1h = cursor.fetchone()[0]
print(f"✅ New signals (last 1h): {new_1h}")

# 5. Последние 5 сигналов
cursor.execute("SELECT id, symbol, entry_price, timestamp FROM signals ORDER BY timestamp DESC LIMIT 5")
print("\n✅ Latest 5 signals:")
for row in cursor.fetchall():
    print(f"  #{row[0]} {row[1]} @ ${row[2]} ({row[3]})")

# 6. Сигналы из логов поиска
cursor.execute("SELECT symbol, COUNT(*) FROM signals GROUP BY symbol ORDER BY COUNT(*) DESC")
print("\n✅ Signals by symbol:")
for row in cursor.fetchall():
    print(f"  {row[0]}: {row[1]} signals")

conn.close()

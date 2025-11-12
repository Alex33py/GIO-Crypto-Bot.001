# -*- coding: utf-8 -*-
"""
Инициализация таблицы signals в БД
"""
import sqlite3
import os

# Путь к БД
DB_PATH = "data/gio_crypto_bot.db"

print(f"📂 Открываем БД: {DB_PATH}")

# Подключаемся
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Проверяем существующие таблицы
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [t[0] for t in cursor.fetchall()]

print(f"📊 Существующие таблицы ({len(tables)}):")
for table in tables:
    print(f"   • {table}")

# Проверяем наличие signals
if 'signals' in tables:
    print("\n✅ Таблица 'signals' уже существует!")

    # Показываем структуру
    cursor.execute("PRAGMA table_info(signals)")
    columns = cursor.fetchall()
    print(f"\n📋 Структура таблицы signals ({len(columns)} колонок):")
    for col in columns:
        print(f"   • {col[1]} ({col[2]})")
else:
    print("\n❌ Таблица 'signals' НЕ существует!")
    print("🔧 Создаём таблицу...")

    # Создаём таблицу
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS signals (
            id INTEGER PRIMARY KEY,
            symbol TEXT NOT NULL,
            direction TEXT NOT NULL,
            entry_price REAL NOT NULL,
            stop_loss REAL,
            take_profit REAL,
            tp1 REAL,
            tp2 REAL,
            tp3 REAL,
            scenario_id TEXT,
            confidence TEXT,
            timestamp TEXT NOT NULL,
            status TEXT DEFAULT 'PENDING',
            mtf_alignment TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    conn.commit()
    print("✅ Таблица 'signals' создана успешно!")

    # Проверяем
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    new_tables = [t[0] for t in cursor.fetchall()]

    if 'signals' in new_tables:
        print("✅ Проверка: таблица 'signals' теперь существует!")
    else:
        print("❌ Ошибка: таблица не создана!")

conn.close()
print("\n🎯 Готово! Можете перезапускать бота.")

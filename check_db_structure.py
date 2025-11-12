#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Проверка структуры таблицы signals
"""

import sqlite3

db_path = "D:\\GIO.BOT.002\\data\\gio_crypto_bot.db"

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Получаем структуру таблицы signals
    cursor.execute("PRAGMA table_info(signals)")
    columns = cursor.fetchall()

    print("📊 Структура таблицы 'signals':")
    print("=" * 50)
    for col in columns:
        col_id, name, col_type, not_null, default, pk = col
        print(f"  {name} ({col_type})")

    print("\n" + "=" * 50)

    # Проверяем наличие конкретных колонок
    column_names = [col[1] for col in columns]

    if 'roi' in column_names:
        print("✅ Колонка 'roi' существует")
    else:
        print("❌ Колонка 'roi' НЕ существует")

    if 'current_roi' in column_names:
        print("✅ Колонка 'current_roi' существует")
    else:
        print("❌ Колонка 'current_roi' НЕ существует")

    conn.close()

except Exception as e:
    print(f"❌ Ошибка: {e}")

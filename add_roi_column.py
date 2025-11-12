#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Добавление колонки current_roi в таблицу signals
"""

import sqlite3

db_path = "D:\\GIO.BOT.002\\data\\gio_crypto_bot.db"

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Проверяем, существует ли уже колонка
    cursor.execute("PRAGMA table_info(signals)")
    columns = [col[1] for col in cursor.fetchall()]

    if 'current_roi' in columns:
        print("✅ Колонка 'current_roi' уже существует")
    else:
        # Добавляем колонку current_roi
        cursor.execute("""
            ALTER TABLE signals
            ADD COLUMN current_roi REAL DEFAULT 0.0
        """)

        conn.commit()
        print("✅ Колонка 'current_roi' успешно добавлена")

    # Также добавим колонку для текущей цены (если нужно)
    if 'current_price' not in columns:
        cursor.execute("""
            ALTER TABLE signals
            ADD COLUMN current_price REAL DEFAULT 0.0
        """)
        print("✅ Колонка 'current_price' успешно добавлена")

    conn.commit()
    conn.close()

    print("\n📊 Обновлённая структура таблицы 'signals':")

    # Показываем новую структуру
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(signals)")
    columns = cursor.fetchall()

    for col in columns:
        col_id, name, col_type, not_null, default, pk = col
        print(f"  • {name} ({col_type})")

    conn.close()

except Exception as e:
    print(f"❌ Ошибка: {e}")
    import traceback
    traceback.print_exc()

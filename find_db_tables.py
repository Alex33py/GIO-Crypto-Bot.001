import os
import sqlite3

def find_db_tables(root_dir):
    for dirpath, dirnames, filenames in os.walk(root_dir):
        for filename in filenames:
            if filename.endswith('.db'):
                db_path = os.path.join(dirpath, filename)
                try:
                    conn = sqlite3.connect(db_path)
                    cursor = conn.cursor()
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                    tables = cursor.fetchall()
                    print(f"База: {db_path}")
                    if tables:
                        for t in tables:
                            print(f"  - Таблица: {t[0]}")
                    else:
                        print("  - Таблиц нет")
                    conn.close()
                except Exception as e:
                    print(f"Ошибка при открытии {db_path}: {e}")

find_db_tables('D:/GIO.BOT.002')

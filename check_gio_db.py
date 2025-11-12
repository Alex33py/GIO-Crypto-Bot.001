import sqlite3

DB_PATH = r"D:\GIO.BOT.002\gio_crypto_bot.db" 

def check_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Список таблиц
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    print("Таблицы в базе данных:")
    for t in tables:
        print(f" - {t[0]}")

    # Количество записей и пример из таблицы signals
    if ('signals',) in tables:
        cursor.execute("SELECT COUNT(*) FROM signals")
        count = cursor.fetchone()[0]
        print(f"\nКоличество сигналов: {count}")

        cursor.execute("SELECT * FROM signals ORDER BY timestamp DESC LIMIT 5")
        rows = cursor.fetchall()
        print("\nПоследние 5 сигналов:")
        for row in rows:
            print(row)
    else:
        print("\nТаблица signals в базе данных отсутствует.")

    conn.close()

if __name__ == "__main__":
    check_db()

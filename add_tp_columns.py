import sqlite3

# Путь к базе данных
DATABASE_PATH = r"D:/GIO.BOT.002/data/gio_crypto_bot.db"

def add_columns():
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    columns_to_add = ['tp1_hit', 'tp2_hit', 'tp3_hit']

    for col in columns_to_add:
        try:
            cursor.execute(f"ALTER TABLE signals ADD COLUMN {col} INTEGER DEFAULT 0")
            print(f"✅ Колонка {col} успешно добавлена.")
        except sqlite3.OperationalError as e:
            # Ошибка возникает, если колонка уже существует
            print(f"ℹ️ Колонка {col} уже существует или произошла другая ошибка: {e}")

    conn.commit()
    conn.close()

if __name__ == "__main__":
    add_columns()

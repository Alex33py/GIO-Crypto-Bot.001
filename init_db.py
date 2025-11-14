def init_database():
    import sqlite3
    import os

    # Универсальная директория проекта
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

    # Путь к БД:
    # 1) если есть переменная окружения DB_PATH → используем её (Railway/Docker)
    # 2) иначе: ./data/gio_crypto_bot.db (локальный Windows/Linux)
    DB_PATH = os.getenv("DB_PATH", os.path.join(BASE_DIR, "data", "gio_crypto_bot.db"))

    # Создать папку data, если она отсутствует
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

    # Подключение к БД
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print(f"🔧 Створення таблиць у {DB_PATH}...")

    # ============================================
    # ТАБЛИЦЯ 1: signals
    # ============================================
    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS signals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        symbol TEXT NOT NULL,
        direction TEXT NOT NULL,
        entry_price REAL NOT NULL,
        stop_loss REAL,
        take_profit REAL,
        tp1_price REAL,
        tp2_price REAL,
        tp3_price REAL,
        sl_price REAL,
        confidence REAL,
        risk_reward REAL,
        status TEXT DEFAULT 'active',
        scenario_id TEXT,
        scenario_name TEXT,
        scenario_score REAL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        close_time DATETIME,
        current_roi REAL DEFAULT 0,
        tp1_hit INTEGER DEFAULT 0,
        tp2_hit INTEGER DEFAULT 0,
        tp3_hit INTEGER DEFAULT 0
    )
    """
    )

    cursor.execute("CREATE INDEX IF NOT EXISTS idx_signals_symbol ON signals(symbol)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_signals_status ON signals(status)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_signals_timestamp ON signals(timestamp)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_signals_scenario ON signals(scenario_id)")

    print("✅ Таблиця 'signals' створена")

    # ============================================
    # ТАБЛИЦЯ 2: unified_signals
    # ============================================
    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS unified_signals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        symbol TEXT NOT NULL,
        direction TEXT NOT NULL,
        entry_price REAL NOT NULL,
        stop_loss REAL,
        take_profit REAL,
        tp1_price REAL,
        tp2_price REAL,
        tp3_price REAL,
        sl_price REAL,
        confidence REAL,
        risk_reward REAL,
        status TEXT DEFAULT 'ACTIVE',
        scenario_id TEXT,
        scenario_name TEXT,
        scenario_score REAL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        close_time DATETIME,
        current_roi REAL DEFAULT 0
    )
    """
    )

    cursor.execute("CREATE INDEX IF NOT EXISTS idx_unified_signals_symbol ON unified_signals(symbol)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_unified_signals_status ON unified_signals(status)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_unified_signals_timestamp ON unified_signals(timestamp)")

    print("✅ Таблиця 'unified_signals' створена")

    # ============================================
    # ТАБЛИЦЯ 3: large_trades
    # ============================================
    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS large_trades (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        symbol TEXT NOT NULL,
        side TEXT NOT NULL,
        size REAL NOT NULL,
        size_usd REAL NOT NULL,
        price REAL NOT NULL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """
    )

    cursor.execute("CREATE INDEX IF NOT EXISTS idx_large_trades_symbol ON large_trades(symbol)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_large_trades_timestamp ON large_trades(timestamp)")

    print("✅ Таблиця 'large_trades' створена")

    # Commit
    conn.commit()
    print("\n✅ Усі таблиці створені успішно!")

    # Перевірка таблиць
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()

    print("\n📊 Таблиці в БД:")
    for t in tables:
        print(f"  - {t[0]}")

    conn.close()
    print("\n🎉 Ініціалізація БД завершена!")

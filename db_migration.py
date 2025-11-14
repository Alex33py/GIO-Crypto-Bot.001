import sqlite3
import logging
from pathlib import Path


logger = logging.getLogger(__name__)


def migrate_database():
    """Миграция базы данных для таблицы signals"""
    possible_db_paths = [
        "data/gio_crypto_bot.db",
        "gio_crypto_bot.db",
        "data/gio_bot.db",
        "data/gio_crypto.db",
        "signals.db",
        "gio_signals.db",
    ]

    db_path = None
    for path in possible_db_paths:
        if Path(path).exists():
            db_path = path
            logger.info(f"📂 Найдена база данных: {path}")
            break

    if not db_path:
        logger.warning("⚠️ База данных не найдена! Пропускаем миграцию.")
        return False

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Получаем список существующих колонок
        cursor.execute("PRAGMA table_info(signals)")
        columns = [col[1] for col in cursor.fetchall()]

        # Словарь с колонками для добавления: {имя_колонки: тип_данных}
        needed_columns = {
            "close_time": "TEXT",
            "entry": "REAL",
            "stop_loss": "REAL",
            "sl_price": "REAL",
            "quality_score": "REAL DEFAULT 0",
            "risk_reward": "REAL DEFAULT 0",
            "strategy": "TEXT DEFAULT 'unknown'",
            "market_regime": "TEXT DEFAULT 'neutral'",
            "confidence": "TEXT DEFAULT 'medium'",
            "phase": "TEXT DEFAULT 'unknown'",
            "risk_profile": "TEXT DEFAULT 'moderate'",
            "tactic_name": "TEXT DEFAULT 'default'",
            "validation_score": "REAL DEFAULT 0",
            "trigger_score": "REAL DEFAULT 0",
            "tp1_hit": "INTEGER DEFAULT 0",
            "tp2_hit": "INTEGER DEFAULT 0",
            "tp3_hit": "INTEGER DEFAULT 0",
            "realized_roi": "REAL DEFAULT 0",
            "exit_price": "REAL",
            "profit_percent": "REAL",
            "updated_at": "TEXT",
            "tp1_price": "REAL",
            "tp2_price": "REAL",
            "tp3_price": "REAL",
        }


        # Добавляем отсутствующие колонки
        for col_name, col_type in needed_columns.items():
            if col_name not in columns:
                logger.info(f"🔧 Добавляем колонку {col_name}...")
                try:
                    cursor.execute(f"ALTER TABLE signals ADD COLUMN {col_name} {col_type}")
                    conn.commit()
                    logger.info(f"✅ Колонка {col_name} добавлена.")
                except sqlite3.OperationalError as e:
                    logger.warning(f"⚠️ Не удалось добавить колонку {col_name}: {e}")

        # Выводим финальный список колонок
        cursor.execute("PRAGMA table_info(signals)")
        columns_info = cursor.fetchall()
        logger.info(f"📋 Текущие колонки в таблице 'signals': {', '.join([col[1] for col in columns_info])}")

        return True
    except sqlite3.OperationalError as e:
        logger.error(f"❌ Ошибка миграции: {e}")
        return False
    finally:
        conn.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    migrate_database()


# python db_migration.py

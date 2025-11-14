#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Менеджер для работы с unified_signals с поддержкой AI метаданных
"""

import sqlite3
import os
import json
from datetime import datetime
from typing import Dict, Optional, List
from config.settings import DATA_DIR, logger

DB_PATH = os.path.join(DATA_DIR, "gio_crypto_bot.db")

def init_database():
    """Создаёт/обновляет схему БД с поддержкой AI metadata"""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT name FROM sqlite_master
                WHERE type='table' AND name='unified_signals'
            """)

            table_exists = cursor.fetchone() is not None

            if not table_exists:
                cursor.execute("""
                    CREATE TABLE unified_signals (
                        id INTEGER PRIMARY KEY,
                        symbol TEXT NOT NULL,
                        direction TEXT NOT NULL,
                        entry_price REAL NOT NULL,
                        scenario_id TEXT,
                        scenario_score REAL,
                        confidence REAL,
                        tp1_price REAL,
                        tp2_price REAL,
                        tp3_price REAL,
                        sl_price REAL,
                        tp1_hit INTEGER DEFAULT 0,
                        tp2_hit INTEGER DEFAULT 0,
                        tp3_hit INTEGER DEFAULT 0,
                        sl_hit INTEGER DEFAULT 0,
                        current_roi REAL DEFAULT 0,
                        status TEXT DEFAULT 'ACTIVE',
                        timestamp TEXT,
                        updated_at TEXT,
                        ai_metadata TEXT
                    )
                """)
                logger.info("✅ Таблица unified_signals создана с AI metadata")
            else:
                cursor.execute("PRAGMA table_info(unified_signals)")
                columns = [row[1] for row in cursor.fetchall()]

                if 'ai_metadata' not in columns:
                    cursor.execute("ALTER TABLE unified_signals ADD COLUMN ai_metadata TEXT")
                    logger.info("✅ Добавлена колонка ai_metadata")

            conn.commit()

    except Exception as e:
        logger.error(f"❌ Ошибка init_database: {e}")


def save_signal(signal_data: Dict, ai_metadata: Optional[Dict] = None) -> bool:
    """Сохраняет сигнал в unified_signals с AI метаданными"""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()

            ai_json = json.dumps(ai_metadata) if ai_metadata else None

            INSERT_SQL = """
            INSERT OR REPLACE INTO unified_signals (
                id, symbol, direction, entry_price,
                scenario_id, scenario_score, confidence,
                tp1_price, tp2_price, tp3_price, sl_price,
                status, timestamp, updated_at, ai_metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """

            cursor.execute(
                INSERT_SQL,
                (
                    signal_data.get("id"),
                    signal_data.get("symbol"),
                    signal_data.get("direction"),
                    signal_data.get("entry_price"),
                    signal_data.get("scenario_id"),
                    signal_data.get("scenario_score"),
                    signal_data.get("confidence"),
                    signal_data.get("tp1_price"),
                    signal_data.get("tp2_price"),
                    signal_data.get("tp3_price"),
                    signal_data.get("sl_price"),
                    signal_data.get("status", "ACTIVE"),
                    datetime.now().isoformat(),
                    datetime.now().isoformat(),
                    ai_json
                ),
            )

            conn.commit()
            logger.info(f"✅ Signal saved with AI metadata: {signal_data['id']}")
            return True

    except Exception as e:
        logger.error(f"❌ Error saving signal: {e}")
        return False


def save_signal_to_unified(signal, ai_metadata: Optional[Dict] = None) -> bool:
    """
    Сохраняет EnhancedTradingSignal в unified_signals с AI метаданными

    Args:
        signal: Объект EnhancedTradingSignal
        ai_metadata: Словарь с AI метаданными (опционально)

    Returns:
        bool: True если успешно сохранено
    """
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()

            # Генерируем ID
            signal_id = int(datetime.now().timestamp())

            # Конвертируем SELL → SHORT, BUY → LONG
            direction = "LONG" if signal.side == "BUY" else "SHORT"

            # Конвертируем AI metadata в JSON
            ai_json = json.dumps(ai_metadata) if ai_metadata else None

            INSERT_SQL = """
            INSERT OR REPLACE INTO unified_signals (
                id, symbol, direction, entry_price,
                scenario_id, scenario_score, confidence,
                tp1_price, tp2_price, tp3_price, sl_price,
                status, timestamp, updated_at, ai_metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """

            cursor.execute(INSERT_SQL, (
                signal_id,
                signal.symbol,
                direction,
                signal.price_entry,
                signal.scenario_id,
                signal.confidence_score * 100,
                signal.confidence_score * 100,
                signal.tp1_price,
                signal.tp2_price,
                signal.tp3_price,
                signal.sl_price,
                "ACTIVE",
                datetime.now().isoformat(),
                datetime.now().isoformat(),
                ai_json
            ))

            conn.commit()
            logger.info(f"✅ Signal saved to unified_signals with AI: {signal_id}")
            return True

    except Exception as e:
        logger.error(f"❌ Error saving signal to unified_signals: {e}")
        return False


def update_signal_roi(signal_id: int, current_price: float) -> Optional[Dict]:
    """Обновляет ROI и статус сигнала"""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT symbol, direction, entry_price,
                       tp1_price, tp2_price, tp3_price, sl_price,
                       tp1_hit, tp2_hit, tp3_hit, sl_hit
                FROM unified_signals
                WHERE id = ? AND status = 'ACTIVE'
            """,
                (signal_id,),
            )

            row = cursor.fetchone()
            if not row:
                return None

            (symbol, direction, entry, tp1_price, tp2_price, tp3_price, sl_price, tp1_hit, tp2_hit, tp3_hit, sl_hit) = row

            if direction == "LONG":
                roi = ((current_price - entry) / entry) * 100
            else:
                roi = ((entry - current_price) / entry) * 100

            updates = {"current_roi": roi}

            if direction == "LONG":
                if current_price >= tp1_price and not tp1_hit:
                    updates["tp1_hit"] = 1
                if current_price >= tp2_price and not tp2_hit:
                    updates["tp2_hit"] = 1
                if current_price >= tp3_price and not tp3_hit:
                    updates["tp3_hit"] = 1
                    updates["status"] = "CLOSED"
                if sl_price and current_price <= sl_price and not sl_hit:
                    updates["sl_hit"] = 1
                    updates["status"] = "CLOSED"
            else:
                if current_price <= tp1_price and not tp1_hit:
                    updates["tp1_hit"] = 1
                if current_price <= tp2_price and not tp2_hit:
                    updates["tp2_hit"] = 1
                if current_price <= tp3_price and not tp3_hit:
                    updates["tp3_hit"] = 1
                    updates["status"] = "CLOSED"
                if sl_price and current_price >= sl_price and not sl_hit:
                    updates["sl_hit"] = 1
                    updates["status"] = "CLOSED"

            update_fields = ", ".join([f"{k} = ?" for k in updates.keys()])
            update_values = list(updates.values()) + [datetime.now().isoformat(), signal_id]

            cursor.execute(
                f"""
                UPDATE unified_signals
                SET {update_fields}, updated_at = ?
                WHERE id = ?
            """,
                update_values,
            )

            conn.commit()
            logger.debug(f"✅ Signal updated: {signal_id} | ROI: {roi:.2f}%")
            return updates

    except Exception as e:
        logger.error(f"❌ Error updating signal: {e}")
        return None


def get_active_signals() -> List[Dict]:
    """Получает все активные сигналы"""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT * FROM unified_signals
                WHERE status = 'ACTIVE'
                ORDER BY scenario_score DESC
            """
            )

            signals = []
            for row in cursor.fetchall():
                signal = dict(row)

                if signal.get('ai_metadata'):
                    try:
                        signal['ai_metadata'] = json.loads(signal['ai_metadata'])
                    except:
                        signal['ai_metadata'] = None

                signals.append(signal)

            return signals

    except Exception as e:
        logger.error(f"❌ Error fetching active signals: {e}")
        return []


def get_latest_signals(limit: int = 5) -> List[Dict]:
    """Получает последние сигналы с AI метаданными"""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT * FROM unified_signals
                ORDER BY timestamp DESC
                LIMIT ?
            """,
                (limit,)
            )

            signals = []
            for row in cursor.fetchall():
                signal = dict(row)

                if signal.get('ai_metadata'):
                    try:
                        signal['ai_metadata'] = json.loads(signal['ai_metadata'])
                    except:
                        signal['ai_metadata'] = None

                if signal.get('timestamp'):
                    try:
                        signal['timestamp'] = datetime.fromisoformat(signal['timestamp'])
                    except:
                        pass

                signals.append(signal)

            logger.info(f"📊 Получено {len(signals)} последних сигналов")
            return signals

    except Exception as e:
        logger.error(f"❌ Error fetching latest signals: {e}")
        return []


init_database()

# -*- coding: utf-8 -*-
"""
Signal Analytics - Аналитика торговых сигналов
Статистика по сценариям, стратегиям и рыночным режимам
"""

import sqlite3
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict

from config.settings import logger, DATABASE_PATH

# 1️⃣ CONFIDENCE THRESHOLD = 0.15
MIN_CONFIDENCE = 0.15  # ← Оптимизировано из BACKTEST (улучшило WR на 4.5%)

# 2️⃣ ADX ПО ТИПАМ СЦЕНАРИЕВ
def get_adx_threshold(scenario_type: str) -> tuple:
    """Получить диапазон ADX для типа сценария"""
    thresholds = {
        "MOMENTUM": (25, 75),      # Нужен сильный тренд
        "PULLBACK": (10, 20),      # Нужен слабый тренд
        "BREAKOUT": (25, 75),      # Ускорение тренда
        "MEAN_REVERSION": (10, 20),
        "WYCKOFF": (10, 50),       # Широкий диапазон
    }
    return thresholds.get(scenario_type, (15, 75))

def validate_adx_for_scenario(scenario_type: str, adx_value: float) -> bool:
    """Проверить ADX для конкретного сценария"""
    min_adx, max_adx = get_adx_threshold(scenario_type)
    return min_adx < adx_value < max_adx

# 3️⃣ CVD + VOLUME BONUS (+10%)
CVD_VOLUME_CONFIDENCE_BONUS = 1.1

def apply_cvd_volume_bonus(confidence: float, cvd_signal: str, volume_signal: str) -> float:
    """Добавить +10% confidence если CVD и Volume совпадают"""
    if cvd_signal == volume_signal and volume_signal in ["BULLISH", "BEARISH"]:
        return confidence * CVD_VOLUME_CONFIDENCE_BONUS
    return confidence

# 4️⃣ ДЕТАЛЬНОЕ ЛОГИРОВАНИЕ СИГНАЛОВ
def log_signal_detailed(signal: dict, logger_obj):
    """Логировать сигнал со ВСЕМИ деталями"""
    logger_obj.info(f"""
✅ SIGNAL GENERATED (OPTIMIZED v4.0):
   ├─ Scenario: {signal.get('scenario_id', 'N/A')} ({signal.get('scenario_name', 'N/A')})
   ├─ Symbol: {signal.get('symbol', 'N/A')}
   ├─ Direction: {signal.get('direction', 'N/A')}
   ├─ Status: {signal.get('status', 'N/A')} (confidence: {signal.get('confidence', 0):.2f})
   ├─ Entry: ${signal.get('entry_price', 0):.2f}
   ├─ SL: ${signal.get('stop_loss', 0):.2f}
   ├─ TP: ${signal.get('take_profit', 0):.2f}
   ├─ RR Ratio: 1:{signal.get('rr_ratio', 0):.2f}
   ├─ Quality Filters:
   │  ├─ ADX: {signal.get('adx_value', 0):.2f}
   │  ├─ RSI: {signal.get('rsi_value', 0):.2f}
   │  ├─ Volume: {signal.get('volume_ratio', 0):.2f}x
   │  ├─ MTF: {signal.get('mtf_alignment', 0):.1f}/3
   │  └─ CVD: {signal.get('cvd_signal', 'N/A')}
   └─ Timestamp: {signal.get('timestamp', 'N/A')}
    """)

class SignalAnalytics:
    """Класс для аналитики торговых сигналов"""

    def __init__(self, db_path: str = None):
        self.db_path = db_path or DATABASE_PATH
        logger.info(f"✅ SignalAnalytics инициализирован (DB: {self.db_path})")

    def get_stats_by_scenario(self, days: int = 30) -> Dict:
        """
        Статистика по каждому сценарию

        Args:
            days: Период анализа (дней)

        Returns:
            Dict с статистикой по сценариям
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            query = f"""
                SELECT
                    scenario_id,
                    COUNT(*) as total_signals,
                    SUM(CASE WHEN profit_percent > 0 THEN 1 ELSE 0 END) as winning,
                    SUM(CASE WHEN profit_percent < 0 THEN 1 ELSE 0 END) as losing,
                    AVG(profit_percent) as avg_roi,
                    MAX(profit_percent) as max_profit,
                    MIN(profit_percent) as max_loss,
                    AVG(quality_score) as avg_quality,
                    AVG(risk_reward) as avg_rr
                FROM signals
                WHERE timestamp > datetime('now', '-{days} days')
                    AND exit_price IS NOT NULL
                    AND scenario_id IS NOT NULL
                GROUP BY scenario_id
                ORDER BY total_signals DESC
            """

            cursor.execute(query)
            rows = cursor.fetchall()
            conn.close()

            stats = {}
            for row in rows:
                scenario_id = row[0]
                total = row[1]
                winning = row[2] or 0
                losing = row[3] or 0

                stats[scenario_id] = {
                    "total_signals": total,
                    "winning": winning,
                    "losing": losing,
                    "win_rate": (winning / total * 100) if total > 0 else 0.0,
                    "avg_roi": row[4] or 0.0,
                    "max_profit": row[5] or 0.0,
                    "max_loss": row[6] or 0.0,
                    "avg_quality": row[7] or 0.0,
                    "avg_rr": row[8] or 0.0,
                }

            return stats

        except Exception as e:
            logger.error(f"❌ Ошибка get_stats_by_scenario: {e}")
            return {}

    def get_stats_by_strategy(self, days: int = 30) -> Dict:
        """
        Статистика по стратегиям

        Args:
            days: Период анализа (дней)

        Returns:
            Dict с статистикой по стратегиям
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            query = f"""
                SELECT
                    strategy,
                    COUNT(*) as total_signals,
                    SUM(CASE WHEN profit_percent > 0 THEN 1 ELSE 0 END) as winning,
                    AVG(profit_percent) as avg_roi,
                    AVG(quality_score) as avg_quality,
                    COUNT(DISTINCT symbol) as symbols_count
                FROM signals
                WHERE timestamp > datetime('now', '-{days} days')
                    AND exit_price IS NOT NULL
                    AND strategy IS NOT NULL
                GROUP BY strategy
                ORDER BY total_signals DESC
            """

            cursor.execute(query)
            rows = cursor.fetchall()
            conn.close()

            stats = {}
            for row in rows:
                strategy = row[0]
                total = row[1]
                winning = row[2] or 0

                stats[strategy] = {
                    "total_signals": total,
                    "winning": winning,
                    "win_rate": (winning / total * 100) if total > 0 else 0.0,
                    "avg_roi": row[3] or 0.0,
                    "avg_quality": row[4] or 0.0,
                    "symbols_count": row[5] or 0,
                }

            return stats

        except Exception as e:
            logger.error(f"❌ Ошибка get_stats_by_strategy: {e}")
            return {}

    def get_stats_by_market_regime(self, days: int = 30) -> Dict:
        """
        Статистика по рыночным режимам

        Args:
            days: Период анализа (дней)

        Returns:
            Dict с статистикой по режимам
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            query = f"""
                SELECT
                    market_regime,
                    COUNT(*) as total_signals,
                    SUM(CASE WHEN profit_percent > 0 THEN 1 ELSE 0 END) as winning,
                    AVG(profit_percent) as avg_roi,
                    strategy
                FROM signals
                WHERE timestamp > datetime('now', '-{days} days')
                    AND exit_price IS NOT NULL
                    AND market_regime IS NOT NULL
                GROUP BY market_regime, strategy
                ORDER BY market_regime, total_signals DESC
            """

            cursor.execute(query)
            rows = cursor.fetchall()
            conn.close()

            # Группируем по режиму
            stats = defaultdict(lambda: {
                "total_signals": 0,
                "winning": 0,
                "win_rate": 0.0,
                "avg_roi": 0.0,
                "best_strategy": None,
                "strategies": {}
            })

            for row in rows:
                regime = row[0]
                total = row[1]
                winning = row[2] or 0
                avg_roi = row[3] or 0.0
                strategy = row[4]

                stats[regime]["total_signals"] += total
                stats[regime]["winning"] += winning
                stats[regime]["strategies"][strategy] = {
                    "total": total,
                    "winning": winning,
                    "win_rate": (winning / total * 100) if total > 0 else 0.0,
                    "avg_roi": avg_roi
                }

            # Рассчитываем win_rate и определяем лучшую стратегию
            for regime, data in stats.items():
                total = data["total_signals"]
                if total > 0:
                    data["win_rate"] = (data["winning"] / total * 100)

                # Находим лучшую стратегию для режима
                if data["strategies"]:
                    best = max(
                        data["strategies"].items(),
                        key=lambda x: x[1]["win_rate"]
                    )
                    data["best_strategy"] = best[0]
                    data["best_strategy_win_rate"] = best[1]["win_rate"]

            return dict(stats)

        except Exception as e:
            logger.error(f"❌ Ошибка get_stats_by_market_regime: {e}")
            return {}

    def get_stats_by_confidence(self, days: int = 30) -> Dict:
        """
        Статистика по уровням уверенности

        Args:
            days: Период анализа (дней)

        Returns:
            Dict с статистикой по confidence levels
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            query = f"""
                SELECT
                    confidence,
                    COUNT(*) as total_signals,
                    SUM(CASE WHEN profit_percent > 0 THEN 1 ELSE 0 END) as winning,
                    AVG(profit_percent) as avg_roi,
                    AVG(quality_score) as avg_quality
                FROM signals
                WHERE timestamp > datetime('now', '-{days} days')
                    AND exit_price IS NOT NULL
                    AND confidence IS NOT NULL
                GROUP BY confidence
                ORDER BY
                    CASE confidence
                        WHEN 'high' THEN 1
                        WHEN 'medium' THEN 2
                        WHEN 'low' THEN 3
                    END
            """

            cursor.execute(query)
            rows = cursor.fetchall()
            conn.close()

            stats = {}
            for row in rows:
                confidence = row[0]
                total = row[1]
                winning = row[2] or 0

                stats[confidence] = {
                    "total_signals": total,
                    "winning": winning,
                    "win_rate": (winning / total * 100) if total > 0 else 0.0,
                    "avg_roi": row[3] or 0.0,
                    "avg_quality": row[4] or 0.0,
                }

            return stats

        except Exception as e:
            logger.error(f"❌ Ошибка get_stats_by_confidence: {e}")
            return {}

    def get_top_performing_scenarios(self, days: int = 30, limit: int = 5) -> List[Dict]:
        """
        Топ-N лучших сценариев по win rate

        Args:
            days: Период анализа (дней)
            limit: Количество сценариев

        Returns:
            List сценариев отсортированных по win_rate
        """
        stats = self.get_stats_by_scenario(days)

        # Фильтруем сценарии с минимум 5 сигналами
        filtered = {
            k: v for k, v in stats.items()
            if v["total_signals"] >= 5
        }

        # Сортируем по win_rate
        sorted_scenarios = sorted(
            filtered.items(),
            key=lambda x: x[1]["win_rate"],
            reverse=True
        )

        return [
            {"scenario_id": k, **v}
            for k, v in sorted_scenarios[:limit]
        ]

    def get_overall_stats(self, days: int = 30) -> Dict:
        """
        Общая статистика за период

        Args:
            days: Период анализа (дней)

        Returns:
            Dict с общей статистикой
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            query = f"""
                SELECT
                    COUNT(*) as total_signals,
                    SUM(CASE WHEN profit_percent > 0 THEN 1 ELSE 0 END) as winning,
                    SUM(CASE WHEN profit_percent < 0 THEN 1 ELSE 0 END) as losing,
                    AVG(profit_percent) as avg_roi,
                    MAX(profit_percent) as max_profit,
                    MIN(profit_percent) as max_loss,
                    AVG(quality_score) as avg_quality,
                    AVG(risk_reward) as avg_rr,
                    COUNT(DISTINCT symbol) as symbols_traded,
                    COUNT(DISTINCT scenario_id) as scenarios_used
                FROM signals
                WHERE timestamp > datetime('now', '-{days} days')
                    AND exit_price IS NOT NULL
            """

            cursor.execute(query)
            row = cursor.fetchone()
            conn.close()

            if not row or row[0] == 0:
                return {
                    "total_signals": 0,
                    "winning": 0,
                    "losing": 0,
                    "win_rate": 0.0,
                    "avg_roi": 0.0,
                    "max_profit": 0.0,
                    "max_loss": 0.0,
                    "avg_quality": 0.0,
                    "avg_rr": 0.0,
                    "symbols_traded": 0,
                    "scenarios_used": 0,
                }

            total = row[0]
            winning = row[1] or 0

            return {
                "total_signals": total,
                "winning": winning,
                "losing": row[2] or 0,
                "win_rate": (winning / total * 100) if total > 0 else 0.0,
                "avg_roi": row[3] or 0.0,
                "max_profit": row[4] or 0.0,
                "max_loss": row[5] or 0.0,
                "avg_quality": row[6] or 0.0,
                "avg_rr": row[7] or 0.0,
                "symbols_traded": row[8] or 0,
                "scenarios_used": row[9] or 0,
            }

        except Exception as e:
            logger.error(f"❌ Ошибка get_overall_stats: {e}")
            return {}


# Экспорт
__all__ = ["SignalAnalytics"]

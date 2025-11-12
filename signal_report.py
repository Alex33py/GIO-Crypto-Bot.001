import matplotlib.pyplot as plt
import sqlite3
from collections import Counter
from datetime import datetime, timedelta

DATABASE_PATH = r"D:/GIO.BOT.002/data/gio_crypto_bot.db"


def get_signal_stats(days=30):
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute(f"""
    SELECT
        COUNT(*) as total,
        SUM(CASE WHEN current_roi > 0 THEN 1 ELSE 0 END) as winning,
        SUM(CASE WHEN current_roi < 0 THEN 1 ELSE 0 END) as losing,
        AVG(current_roi) as avg_profit,
        MAX(current_roi) as max_profit,
        MIN(current_roi) as max_loss
    FROM signals
    WHERE timestamp > datetime('now', '-{days} days')
          AND close_time IS NOT NULL
""")

    row = cursor.fetchone()
    conn.close()
    if not row or row[0] == 0:
        return None
    return {
        "total": row[0],
        "winning": row[1],
        "losing": row[2],
        "win_rate": row[1] / row[0] * 100,
        "avg_profit": row[3],
        "max_profit": row[4],
        "max_loss": row[5],
    }

def get_tp_hits(days=30):
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute(f"""
    SELECT tp1_hit, tp2_hit, tp3_hit FROM signals
    WHERE timestamp > datetime('now', '-{days} days')
      AND close_time IS NOT NULL
""")

    rows = cursor.fetchall()
    conn.close()

    tp1_hits = sum(r[0] for r in rows)
    tp2_hits = sum(r[1] for r in rows)
    tp3_hits = sum(r[2] for r in rows)
    total = len(rows) if rows else 0

    return {
        "tp1_hits": tp1_hits,
        "tp2_hits": tp2_hits,
        "tp3_hits": tp3_hits,
        "total": total,
        "tp1_rate": (tp1_hits / total * 100) if total > 0 else 0,
        "tp2_rate": (tp2_hits / total * 100) if total > 0 else 0,
        "tp3_rate": (tp3_hits / total * 100) if total > 0 else 0,
    }


def plot_winrate_pie(win_rate):
    labels = ['Winning', 'Losing']
    sizes = [win_rate, 100 - win_rate]
    colors = ['#4CAF50', '#F44336']
    plt.figure(figsize=(5,5))
    plt.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=140)
    plt.title('Win Rate')
    plt.show()

def plot_tp_rates(tp_rates):
    labels = ['TP1', 'TP2', 'TP3']
    rates = [tp_rates['tp1_rate'], tp_rates['tp2_rate'], tp_rates['tp3_rate']]
    plt.figure(figsize=(7,4))
    plt.bar(labels, rates, color=['#2196F3', '#FFC107', '#9C27B0'])
    plt.ylabel('Hit Rate (%)')
    plt.title('Take Profit Hit Rates')
    plt.ylim(0, 100)
    plt.show()

if __name__ == "__main__":
    stats = get_signal_stats(days=30)
    tp_hits = get_tp_hits(days=30)

    if not stats:
        print("Нет данных для отчёта")
    else:
        print("=== Статистика сигналов за последние 30 дней ===")
        print(f"Всего сигналов: {stats['total']}")
        print(f"Выигрышных: {stats['winning']}")
        print(f"Проигрышных: {stats['losing']}")
        print(f"Win Rate (WR): {stats['win_rate']:.2f}%")
        print(f"Средняя прибыль: {stats['avg_profit']:.2f}%")
        print(f"Максимальная прибыль: {stats['max_profit']:.2f}%")
        print(f"Максимальный убыток: {stats['max_loss']:.2f}%")

        print("\n=== Достижения тейк-профитов ===")
        print(f"TP1 Hits: {tp_hits['tp1_hits']} из {tp_hits['total']} ({tp_hits['tp1_rate']:.2f}%)")
        print(f"TP2 Hits: {tp_hits['tp2_hits']} из {tp_hits['total']} ({tp_hits['tp2_rate']:.2f}%)")
        print(f"TP3 Hits: {tp_hits['tp3_hits']} из {tp_hits['total']} ({tp_hits['tp3_rate']:.2f}%)")

        plot_winrate_pie(stats['win_rate'])
        plot_tp_rates(tp_hits)


#  python signal_report.py

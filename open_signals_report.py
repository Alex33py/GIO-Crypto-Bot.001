import sqlite3
from collections import Counter

DATABASE_PATH = r"D:/GIO.BOT.002/data/gio_crypto_bot.db"

def get_open_signal_stats():
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    # Общее число открытых сигналов (без close_time)
    cursor.execute("SELECT COUNT(*) FROM signals WHERE close_time IS NULL")
    total_open = cursor.fetchone()[0]

    # Средний confidence по открытым сигналам (confidence хранится как текст, возможно строка с числом)
    cursor.execute("SELECT confidence FROM signals WHERE close_time IS NULL")
    confs = cursor.fetchall()
    confidences = []
    for c in confs:
        try:
            confidences.append(float(c[0]))
        except:
            pass
    avg_confidence = sum(confidences) / len(confidences) if confidences else 0

    # Распределение по direction (LONG/SHORT)
    cursor.execute("SELECT direction FROM signals WHERE close_time IS NULL")
    dirs = [row[0] for row in cursor.fetchall()]
    direction_counts = Counter(dirs)

    # Распределение по торговым парам (symbol)
    cursor.execute("SELECT symbol FROM signals WHERE close_time IS NULL")
    syms = [row[0] for row in cursor.fetchall()]
    symbol_counts = Counter(syms)

    conn.close()

    return {
        "total_open": total_open,
        "avg_confidence": avg_confidence,
        "direction_counts": direction_counts,
        "symbol_counts": symbol_counts
    }

if __name__ == "__main__":
    stats = get_open_signal_stats()
    print(f"Всего открытых сигналов: {stats['total_open']}")
    print(f"Средний confidence: {stats['avg_confidence']:.3f}")
    print("Распределение по направлениям (direction):")
    for d, cnt in stats["direction_counts"].items():
        print(f"  {d}: {cnt}")
    print("Распределение по торговым парам (symbol):")
    for s, cnt in stats["symbol_counts"].items():
        print(f"  {s}: {cnt}")

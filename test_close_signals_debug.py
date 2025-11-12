import sqlite3
import datetime

DATABASE_PATH = r"D:/GIO.BOT.002/data/gio_crypto_bot.db"

def close_signal(signal_id, exit_price, roi, tp_flags):
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    close_time = datetime.datetime.now(datetime.timezone.utc).isoformat()
    cursor.execute("""
        UPDATE signals SET close_time=?, current_roi=?, current_price=?,
        tp1_hit=?, tp2_hit=?, tp3_hit=?, status='closed'
        WHERE id=?
    """, (
        close_time, roi, exit_price,
        tp_flags.get('tp1_hit', 0), tp_flags.get('tp2_hit', 0), tp_flags.get('tp3_hit', 0),
        signal_id))
    conn.commit()
    conn.close()
    print(f"Signal {signal_id} closed at price {exit_price} with ROI {roi:.2f}% and TP hits {tp_flags}")

def check_signals(test_prices):
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, symbol, direction, entry_price, tp1, tp2, tp3, stop_loss FROM signals WHERE status = 'active'")
    signals = cursor.fetchall()

    if not signals:
        print("No active signals found.")
        conn.close()
        return

    print(f"Checking {len(signals)} active signals")

    for sig in signals:
        signal_id, symbol, direction, entry_price, tp1, tp2, tp3, stop_loss = sig
        price = test_prices.get(symbol)
        if price is None:
            print(f"No test price for symbol {symbol}, skipping signal {signal_id}")
            continue

        tp_flags = {'tp1_hit': 0, 'tp2_hit': 0, 'tp3_hit': 0}
        roi = 0

        if direction == 'LONG':
            if price >= tp3:
                tp_flags = {'tp1_hit':1, 'tp2_hit':1, 'tp3_hit':1}
                roi = (price - entry_price) / entry_price * 100
                close_signal(signal_id, price, roi, tp_flags)
            elif price >= tp2:
                tp_flags = {'tp1_hit':1, 'tp2_hit':1}
                roi = (price - entry_price) / entry_price * 100
                close_signal(signal_id, price, roi, tp_flags)
            elif price >= tp1:
                tp_flags = {'tp1_hit':1}
                roi = (price - entry_price) / entry_price * 100
                close_signal(signal_id, price, roi, tp_flags)
            elif price <= stop_loss:
                roi = (price - entry_price) / entry_price * 100
                close_signal(signal_id, price, roi, tp_flags)
            else:
                print(f"Signal {signal_id} not closed, current price {price} below tp1 {tp1}")
        else:
            print(f"Unsupported direction {direction} for signal {signal_id}")

    conn.close()

if __name__ == "__main__":
    test_prices = {
        "ETHUSDT": 3550.0  # Тестовая цена для закрытия сигнала по TP1 или выше
    }
    check_signals(test_prices)

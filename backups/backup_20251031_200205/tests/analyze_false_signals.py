import pandas as pd
import json

# Загрузить последние результаты backtest
df = pd.read_csv('tests/results/backtest_full_sim_20251031_192851.csv')

# Анализ ложных сигналов
losses = df[df['pnl'] < 0]

print("=" * 70)
print("🔍 АНАЛИЗ ЛОЖНЫХ СИГНАЛОВ")
print("=" * 70)

print(f"\n📊 Общая статистика:")
print(f"├─ Всего сделок: {len(df)}")
print(f"├─ Убыточные: {len(losses)} ({len(losses)/len(df)*100:.1f}%)")
print(f"└─ Средний убыток: ${losses['pnl'].mean():.2f}")

print(f"\n🎯 Топ-5 сценариев с ложными сигналами:")
worst = losses.groupby('scenario').agg({
    'pnl': ['count', 'sum', 'mean']
}).round(2)
worst.columns = ['count', 'total_loss', 'avg_loss']
worst = worst.sort_values('count', ascending=False).head(5)
print(worst)

print(f"\n⚠️ ПРОБЛЕМНЫЕ ПАТТЕРНЫ:")
print(f"├─ Проблема #1: Мало уникальных сценариев (31/112)")
print(f"│  └─ Решение: Понизить observation_threshold до 0.03")
print(f"├─ Проблема #2: Все MTF=STRONG (нет дифференциации)")
print(f"│  └─ Решение: Добавить market diversity в simulator")
print(f"└─ Проблема #3: Win Rate 30% (слишком низкий)")
print(f"   └─ Решение: Оптимизировать ADX warmup + scenario weights")

# Сохранить отчёт
with open('tests/results/false_signals_analysis.txt', 'w') as f:
    f.write("ДЕНЬ 2: АНАЛИЗ ЛОЖНЫХ СИГНАЛОВ\n")
    f.write("=" * 70 + "\n")
    f.write(f"Total losses: {len(losses)}\n")
    f.write(f"Avg loss: ${losses['pnl'].mean():.2f}\n")
    f.write("\nTop problematic scenarios:\n")
    f.write(str(worst))

print("\n✅ Отчёт сохранён: tests/results/false_signals_analysis.txt")




# -*- coding: utf-8 -*-
"""
Подготовка training data для ML модели
Маржирует features с результатами торговли
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import pickle

class TrainingDataPreparer:
    """Подготовка данных для обучения ML модели"""

    def __init__(self):
        self.scaler = StandardScaler()

    def load_features(self, features_path):
        """Загрузить вычисленные features"""
        print(f"📥 Загружаю features из {features_path}...")
        df_features = pd.read_csv(features_path)
        df_features['timestamp'] = pd.to_datetime(df_features['timestamp'])

        # ✅ НОВОЕ: Очистить inf/nan сразу
        print(f"   🧹 Очистка inf/nan в features...")
        df_features = df_features.replace([np.inf, -np.inf], np.nan)

        # Заменить NaN на median (или 0 для некоторых features)
        for col in df_features.select_dtypes(include=[np.number]).columns:
            if df_features[col].isna().sum() > 0:
                median_val = df_features[col].median()
                df_features[col].fillna(median_val if not np.isnan(median_val) else 0, inplace=True)

        print(f"   ✅ Загружено {len(df_features)} строк (cleaned)")
        return df_features

    def load_backtest_results(self, backtest_csv):
        """Загрузить результаты backtesta"""
        print(f"📥 Загружаю результаты backtesta из {backtest_csv}...")
        df_trades = pd.read_csv(backtest_csv)
        df_trades['entry_time'] = pd.to_datetime(df_trades['entry_time'])
        print(f"   ✅ Загружено {len(df_trades)} сделок")
        return df_trades

    def merge_features_with_trades(self, df_features, df_trades):
        """Маржировать features с результатами торговли"""
        print(f"\n🔀 Маржирование features с торговыми результатами...")

        merged_list = []

        for idx, trade in df_trades.iterrows():
            entry_time = trade['entry_time']

            # Найти ближайший row перед входом (в пределах 10 минут)
            time_mask = (df_features['timestamp'] <= entry_time) & \
                       (df_features['timestamp'] >= entry_time - pd.Timedelta(minutes=10))

            matching_rows = df_features[time_mask]

            if len(matching_rows) > 0:
                # Взять ближайший
                closest_idx = (matching_rows['timestamp'] - entry_time).abs().idxmin()
                feature_row = df_features.loc[closest_idx].to_dict()

                feature_row['pnl'] = trade['pnl']
                feature_row['pnl_pct'] = trade['pnl_pct']
                feature_row['label'] = 1 if trade['pnl'] > 0 else 0
                feature_row['entry_time'] = entry_time

                merged_list.append(feature_row)

        df_merged = pd.DataFrame(merged_list)
        print(f"   ✅ Маржировано {len(df_merged)} trade samples")

        return df_merged

    def prepare_ml_data(self, df_merged, exclude_cols=['timestamp', 'pnl', 'pnl_pct', 'label', 'entry_time']):
        """Подготовить X (features) и y (labels)"""
        print(f"\n🔧 Подготовка ML data...")

        if len(df_merged) == 0:
            raise ValueError("❌ No samples to process!")

        # Выбрать только числовые features
        feature_cols = [col for col in df_merged.columns
                       if col not in exclude_cols
                       and df_merged[col].dtype in ['float64', 'int64', 'float32', 'int32']]

        print(f"   📊 Всего features: {len(feature_cols)}")
        print(f"   📊 Samples before cleaning: {len(df_merged)}")

        # Создать чистый DataFrame
        df_clean = df_merged[feature_cols + ['label']].copy()

        # Проверить inf/nan
        print(f"   🔍 Проверка на inf/nan...")
        for col in feature_cols:
            inf_count = np.isinf(df_clean[col]).sum()
            nan_count = df_clean[col].isna().sum()
            if inf_count > 0 or nan_count > 0:
                print(f"      ⚠️ {col}: {inf_count} inf, {nan_count} nan")

        # Удалить только полностью NaN строки
        df_clean = df_clean.dropna(subset=['label'])

        # Заменить remaining inf/nan
        df_clean = df_clean.replace([np.inf, -np.inf], np.nan)

        for col in feature_cols:
            if df_clean[col].isna().any():
                median_val = df_clean[col].median()
                df_clean[col].fillna(median_val if not np.isnan(median_val) else 0, inplace=True)

        print(f"   ✅ Samples after cleaning: {len(df_clean)}")

        if len(df_clean) == 0:
            raise ValueError("❌ All samples removed after cleaning!")

        X = df_clean[feature_cols].values
        y = df_clean['label'].values

        print(f"\n   📊 Final data:")
        print(f"      Features: {X.shape[1]}")
        print(f"      Samples: {X.shape[0]}")
        print(f"      Win Rate: {y.mean()*100:.1f}%")
        print(f"      Wins: {y.sum()} | Losses: {len(y) - y.sum()}")

        # Проверка что нет inf/nan в X
        if np.any(np.isnan(X)) or np.any(np.isinf(X)):
            print("   ⚠️ WARNING: Still has inf/nan, replacing with 0...")
            X = np.nan_to_num(X, nan=0.0, posinf=0.0, neginf=0.0)

        # Масштабировать
        X_scaled = self.scaler.fit_transform(X)

        # Для маленьких датасетов не делаем split если samples < 20
        if len(X_scaled) < 20:
            print(f"\n   ⚠️ Small dataset ({len(X_scaled)} samples)")
            print(f"   Using all data for training (no validation split)")
            return X_scaled, X_scaled, y, y, feature_cols

        # Split на train/val
        try:
            X_train, X_val, y_train, y_val = train_test_split(
                X_scaled, y, test_size=0.2, random_state=42, stratify=y
            )

            print(f"\n   Train set: {X_train.shape[0]} samples")
            print(f"   Val set: {X_val.shape[0]} samples")

            return X_train, X_val, y_train, y_val, feature_cols

        except ValueError as e:
            print(f"\n   ⚠️ Can't stratify (too few samples): {e}")
            print(f"   Using simple split...")

            X_train, X_val, y_train, y_val = train_test_split(
                X_scaled, y, test_size=0.2, random_state=42
            )

            return X_train, X_val, y_train, y_val, feature_cols

    def save_scaler(self, path='models/scaler.pkl'):
        """Сохранить scaler"""
        os.makedirs(os.path.dirname(path), exist_ok=True)
        pickle.dump(self.scaler, open(path, 'wb'))
        print(f"\n💾 Scaler saved: {path}")

def main():
    """Подготовить данные"""
    preparer = TrainingDataPreparer()

    # 1. Загрузить features
    df_features = preparer.load_features(
        "data/ml_training/features/BTCUSDT_features.csv"
    )

    # 2. Загрузить results backtesta
    df_trades = preparer.load_backtest_results(
          "tests/results/backtest_5min_ml_20251104_191414.csv"
    )

    # 3. Маржировать
    df_merged = preparer.merge_features_with_trades(df_features, df_trades)

    # 4. Подготовить X и y
    X_train, X_val, y_train, y_val, feature_cols = preparer.prepare_ml_data(df_merged)

    # 5. Сохранить scaler
    preparer.save_scaler()

    # 6. Сохранить training data
    os.makedirs("data/ml_training/training_data", exist_ok=True)

    np.save("data/ml_training/training_data/X_train.npy", X_train)
    np.save("data/ml_training/training_data/X_val.npy", X_val)
    np.save("data/ml_training/training_data/y_train.npy", y_train)
    np.save("data/ml_training/training_data/y_val.npy", y_val)

    with open("data/ml_training/training_data/feature_cols.pkl", 'wb') as f:
        pickle.dump(feature_cols, f)

    print(f"\n✅ Training data saved!")
    print(f"   X_train shape: {X_train.shape}")
    print(f"   X_val shape: {X_val.shape}")

if __name__ == "__main__":
    main()

# -*- coding: utf-8 -*-
"""
Обучение XGBoost модели для торговли
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import pickle
import xgboost as xgb
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score

class XGBoostTrainer:
    """Обучение XGBoost classifier"""

    def __init__(self):
        self.model = None
        self.feature_importance = None

    def load_training_data(self):
        """Загрузить подготовленные данные"""
        print("📥 Loading training data...")

        X_train = np.load("data/ml_training/training_data/X_train.npy")
        X_val = np.load("data/ml_training/training_data/X_val.npy")
        y_train = np.load("data/ml_training/training_data/y_train.npy")
        y_val = np.load("data/ml_training/training_data/y_val.npy")

        with open("data/ml_training/training_data/feature_cols.pkl", 'rb') as f:
            feature_cols = pickle.load(f)

        print(f"   ✅ Train: {X_train.shape}")
        print(f"   ✅ Val: {X_val.shape}")
        print(f"   ✅ Features: {len(feature_cols)}")

        return X_train, X_val, y_train, y_val, feature_cols

    def train(self, X_train, y_train, X_val, y_val):
        """Обучить XGBoost модель"""
        print("\n🚀 Training XGBoost model...")

        # XGBoost parameters
        params = {
            'objective': 'binary:logistic',
            'eval_metric': 'logloss',
            'max_depth': 6,
            'learning_rate': 0.05,
            'subsample': 0.8,
            'colsample_bytree': 0.8,
            'min_child_weight': 3,
            'gamma': 0.1,
            'random_state': 42,
            'tree_method': 'hist'
        }

        # Create DMatrix
        dtrain = xgb.DMatrix(X_train, label=y_train)
        dval = xgb.DMatrix(X_val, label=y_val)

        # Train
        evals = [(dtrain, 'train'), (dval, 'val')]

        self.model = xgb.train(
            params,
            dtrain,
            num_boost_round=500,
            evals=evals,
            early_stopping_rounds=50,
            verbose_eval=50
        )

        print("\n✅ Model trained!")

    def evaluate(self, X_val, y_val, feature_cols):
        """Оценить модель"""
        print("\n📊 Evaluating model...")

        dval = xgb.DMatrix(X_val)
        y_pred_proba = self.model.predict(dval)
        y_pred = (y_pred_proba > 0.5).astype(int)

        # Метрики
        accuracy = accuracy_score(y_val, y_pred)
        precision = precision_score(y_val, y_pred, zero_division=0)
        recall = recall_score(y_val, y_pred, zero_division=0)
        f1 = f1_score(y_val, y_pred, zero_division=0)

        try:
            auc = roc_auc_score(y_val, y_pred_proba)
        except:
            auc = 0.0

        print("\n" + "="*70)
        print("🎯 MODEL PERFORMANCE")
        print("="*70)
        print(f"\n   Accuracy:  {accuracy:.3f}")
        print(f"   Precision: {precision:.3f}")
        print(f"   Recall:    {recall:.3f}")
        print(f"   F1 Score:  {f1:.3f}")
        print(f"   ROC AUC:   {auc:.3f}")

        # Feature importance
        importance = self.model.get_score(importance_type='gain')

        if importance:
            print("\n📊 TOP 10 MOST IMPORTANT FEATURES:")
            print("="*70)

            # Сортировать по важности
            sorted_features = sorted(importance.items(), key=lambda x: x[1], reverse=True)[:10]

            for idx, (feat_idx, gain) in enumerate(sorted_features, 1):
                feat_name = feature_cols[int(feat_idx.replace('f', ''))] if 'f' in feat_idx else feat_idx
                print(f"   {idx}. {feat_name}: {gain:.2f}")

        print("\n" + "="*70)

        # Предсказание confidence distribution
        print("\n📈 PREDICTION CONFIDENCE DISTRIBUTION:")
        print(f"   High confidence (>0.7): {(y_pred_proba > 0.7).sum()} samples")
        print(f"   Medium conf (0.5-0.7):  {((y_pred_proba > 0.5) & (y_pred_proba <= 0.7)).sum()} samples")
        print(f"   Low confidence (<0.5):  {(y_pred_proba <= 0.5).sum()} samples")

    def save_model(self, path='models/xgboost_trading_model.json'):
        """Сохранить модель"""
        os.makedirs(os.path.dirname(path), exist_ok=True)
        self.model.save_model(path)
        print(f"\n💾 Model saved: {path}")

    def run(self):
        """Полный цикл обучения"""
        print("🚀 XGBOOST TRAINING PIPELINE")
        print("="*70)

        # 1. Load data
        X_train, X_val, y_train, y_val, feature_cols = self.load_training_data()

        # 2. Train
        self.train(X_train, y_train, X_val, y_val)

        # 3. Evaluate
        self.evaluate(X_val, y_val, feature_cols)

        # 4. Save
        self.save_model()

        print("\n✅ Training complete!")

if __name__ == "__main__":
    trainer = XGBoostTrainer()
    trainer.run()

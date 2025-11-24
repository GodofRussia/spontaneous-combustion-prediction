"""
Скрипт для обучения модели предсказания возгораний угля.
Основан на коде из Ygol.ipynb.
"""

import pandas as pd
import numpy as np
import pickle
import logging
from pathlib import Path
from typing import Tuple, List, Any

from sklearn.model_selection import train_test_split, KFold, GridSearchCV
from sklearn.metrics import mean_absolute_error
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from xgboost import XGBRegressor

from data_processing import build_full_dataset

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def accuracy_pm_k(y_true: np.ndarray, y_pred: np.ndarray, k: int = 2) -> float:
    """Точность прогнозов в пределах ±k дней."""
    return (np.abs(y_true - y_pred) <= k).mean()


def train_xgb_with_cv(full_df: pd.DataFrame, max_horizon_days: int = 30):
    """
    Обучает XGBoost на предсказание days_to_fire
    с учётом категориальных признаков, масштабированием числовых и CV.
    """
    df = full_df.copy()

    # фильтруем только те дни, где известен таргет
    mask = (
        df["days_to_fire"].notna() &
        (df["days_to_fire"] >= 0) &
        (df["days_to_fire"] <= max_horizon_days)
    )
    df = df[mask].reset_index(drop=True)

    logger.info(f"Размер выборки для обучения: {df.shape}")

    target_col = "days_to_fire"
    y = df[target_col]

    # Сначала задаём кандидатов в категориальные признаки
    possible_cat_cols = ["coal_grade", "stockyard", "location", "shift"]
    cat_cols = [c for c in possible_cat_cols if c in df.columns]

    # Приводим их к строковому/категориальному типу, чтобы они точно НЕ попали в numeric
    for c in cat_cols:
        df[c] = df[c].astype("string")

    # Теперь определяем числовые признаки
    leak_cols = ["days_to_fire", "fire_start", "fire_in_horizon", "ever_fire"]
    drop_num = leak_cols + ["pile_id"]

    num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    num_cols = [c for c in num_cols if c not in drop_num]

    # Финальный список фич
    feature_cols = num_cols + cat_cols
    X = df[feature_cols]

    logger.info(f"Числовые признаки: {num_cols}")
    logger.info(f"Категориальные признаки: {cat_cols}")

    # train / test split для финальной оценки
    X_train, X_test, y_train, y_test = train_test_split(
        X, y,
        test_size=0.2,
        random_state=42
    )

    # препроцессинг: масштабирование числовых + one-hot для категорий
    preprocessor = ColumnTransformer(
        transformers=[
            ("num", StandardScaler(), num_cols),
            ("cat", OneHotEncoder(handle_unknown="ignore"), cat_cols),
        ]
    )

    xgb_model = XGBRegressor(
        objective="reg:squarederror",
        eval_metric="mae",
        random_state=42,
        n_jobs=-1,
        tree_method="hist"
    )

    pipeline = Pipeline(steps=[
        ("preprocess", preprocessor),
        ("model", xgb_model)
    ])

    param_grid = {
        "model__n_estimators": [300, 500],
        "model__max_depth": [4, 6, 8],
        "model__learning_rate": [0.05, 0.1],
        "model__subsample": [0.7, 1.0],
        "model__colsample_bytree": [0.7, 1.0],
        "model__reg_lambda": [1, 3, 5],
    }

    cv = KFold(n_splits=5, shuffle=True, random_state=42)

    grid = GridSearchCV(
        estimator=pipeline,
        param_grid=param_grid,
        cv=cv,
        scoring="neg_mean_absolute_error",
        verbose=2,
        n_jobs=-1
    )

    logger.info("Запуск GridSearchCV...")
    grid.fit(X_train, y_train)

    logger.info("ЛУЧШИЕ ПАРАМЕТРЫ:")
    logger.info(grid.best_params_)
    logger.info(f"ЛУЧШИЙ MAE на CV: {-grid.best_score_}")

    best_model = grid.best_estimator_

    # Оценка на отложенной тестовой выборке
    y_pred = best_model.predict(X_test)
    mae = mean_absolute_error(y_test, y_pred)
    acc_pm2 = accuracy_pm_k(y_test.values, y_pred, k=2)

    logger.info("\n=== ОЦЕНКА НА TEST ===")
    logger.info(f"MAE: {mae:.3f} дней")
    logger.info(f"Точность ±2 дня: {acc_pm2:.3%}")

    return best_model, feature_cols, num_cols, cat_cols, {"mae": mae, "accuracy_pm2": acc_pm2}


def save_model(model, feature_cols, num_cols, cat_cols, metrics, output_path="models/fire_prediction_model.pkl"):
    """Сохранение модели и артефактов."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    artifacts = {
        "model": model,
        "feature_cols": feature_cols,
        "num_cols": num_cols,
        "cat_cols": cat_cols,
        "metrics": metrics,
        "model_type": "xgboost"
    }

    logger.info(f"Сохранение модели в {output_path}...")
    with open(output_path, "wb") as f:
        pickle.dump(artifacts, f)

    logger.info("Модель успешно сохранена!")


if __name__ == "__main__":
    data_dir = "./data"

    logger.info("Сборка полного датасета...")
    full_df = build_full_dataset(data_dir, horizon_days=3)
    logger.info(f"full_df shape: {full_df.shape}")

    logger.info("\nОбучение XGBoost с CV...")
    best_model, feature_cols, num_cols, cat_cols, metrics = train_xgb_with_cv(full_df, max_horizon_days=30)

    logger.info("\nСохранение модели...")
    save_model(best_model, feature_cols, num_cols, cat_cols, metrics)

    logger.info("\n=== ОБУЧЕНИЕ ЗАВЕРШЕНО ===")
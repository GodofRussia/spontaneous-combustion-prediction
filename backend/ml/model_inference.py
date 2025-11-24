"""
Модуль для загрузки обученной модели и выполнения предсказаний.
"""

import pandas as pd
import numpy as np
import pickle
import logging
from pathlib import Path
from typing import Tuple, Optional, Dict, Any
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class FirePredictionModel:
    """
    Класс для работы с обученной моделью предсказания возгораний.
    """

    def __init__(self, model_path: str = "models/fire_prediction_model.pkl"):
        """
        Инициализация модели.

        Args:
            model_path: Путь к файлу с сохраненной моделью
        """
        self.model_path = Path(model_path)
        self.model = None
        self.feature_cols = None
        self.num_cols = None
        self.cat_cols = None
        self.metrics = None
        self.model_type = None

        self._load_model()

    def _load_model(self) -> None:
        """
        Загрузка модели и артефактов из файла.
        """
        if not self.model_path.exists():
            raise FileNotFoundError(f"Файл модели не найден: {self.model_path}")

        logger.info(f"Загрузка модели из {self.model_path}...")

        with open(self.model_path, "rb") as f:
            artifacts = pickle.load(f)

        self.model = artifacts["model"]
        self.feature_cols = artifacts["feature_cols"]
        self.num_cols = artifacts["num_cols"]
        self.cat_cols = artifacts["cat_cols"]
        self.metrics = artifacts.get("metrics", {})
        self.model_type = artifacts.get("model_type", "unknown")

        logger.info(f"Модель загружена успешно (тип: {self.model_type})")
        logger.info(f"Количество признаков: {len(self.feature_cols)}")
        logger.info(f"Метрики модели: MAE={self.metrics.get('mae', 'N/A'):.3f}, "
                   f"Accuracy±2={self.metrics.get('accuracy_pm2', 'N/A'):.1%}")

    def predict_days_to_fire(self, data: pd.DataFrame) -> np.ndarray:
        """
        Предсказание количества дней до возгорания.

        Args:
            data: DataFrame с признаками (должен содержать все необходимые колонки)

        Returns:
            Массив с предсказанными днями до возгорания
        """
        # Проверка наличия всех необходимых признаков
        missing_cols = set(self.feature_cols) - set(data.columns)
        if missing_cols:
            raise ValueError(f"Отсутствуют необходимые признаки: {missing_cols}")

        # Выбираем только нужные признаки в правильном порядке
        X = data[self.feature_cols].copy()

        # Приводим категориальные признаки к строковому типу
        for col in self.cat_cols:
            if col in X.columns:
                X[col] = X[col].astype("string")

        # Предсказание
        predictions = self.model.predict(X)

        return predictions

    def predict_fire_dates(self, data: pd.DataFrame,
                          date_col: str = "date") -> pd.DataFrame:
        """
        Предсказание дат возгорания для данных.

        Args:
            data: DataFrame с признаками и датой наблюдения
            date_col: Название колонки с датой

        Returns:
            DataFrame с предсказаниями
        """
        if date_col not in data.columns:
            raise ValueError(f"Колонка с датой '{date_col}' не найдена в данных")

        # Предсказываем дни до возгорания
        days_pred = self.predict_days_to_fire(data)

        # Создаем результирующий DataFrame
        result = pd.DataFrame({
            "pile_id": data["pile_id"] if "pile_id" in data.columns else range(len(data)),
            "observation_date": pd.to_datetime(data[date_col]),
            "predicted_days_to_fire": days_pred,
            "predicted_days_to_fire_rounded": np.round(days_pred).astype(int),
        })

        # Вычисляем предсказанную дату возгорания
        result["predicted_fire_date"] = result.apply(
            lambda row: row["observation_date"] + timedelta(days=int(row["predicted_days_to_fire_rounded"])),
            axis=1
        )

        return result

    def predict_single_observation(self, observation: Dict[str, Any],
                                   observation_date: datetime) -> Dict[str, Any]:
        """
        Предсказание для одного наблюдения.

        Args:
            observation: Словарь с признаками
            observation_date: Дата наблюдения

        Returns:
            Словарь с результатами предсказания
        """
        # Создаем DataFrame из одного наблюдения
        df = pd.DataFrame([observation])
        df["date"] = observation_date

        # Получаем предсказание
        result = self.predict_fire_dates(df, date_col="date")

        # Формируем ответ
        prediction = {
            "observation_date": observation_date.isoformat(),
            "predicted_days_to_fire": float(result["predicted_days_to_fire"].iloc[0]),
            "predicted_days_to_fire_rounded": int(result["predicted_days_to_fire_rounded"].iloc[0]),
            "predicted_fire_date": result["predicted_fire_date"].iloc[0].isoformat(),
            "confidence": "high" if result["predicted_days_to_fire"].iloc[0] <= 7 else "medium"
        }

        return prediction

    def get_model_info(self) -> Dict[str, Any]:
        """
        Получение информации о модели.

        Returns:
            Словарь с информацией о модели
        """
        return {
            "model_type": self.model_type,
            "feature_count": len(self.feature_cols),
            "numeric_features": self.num_cols,
            "categorical_features": self.cat_cols,
            "metrics": self.metrics,
            "model_path": str(self.model_path)
        }


def load_model(model_path: str = "models/fire_prediction_model.pkl") -> FirePredictionModel:
    """
    Вспомогательная функция для загрузки модели.

    Args:
        model_path: Путь к файлу модели

    Returns:
        Экземпляр FirePredictionModel
    """
    return FirePredictionModel(model_path)


# Пример использования
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # Загрузка модели
    model = load_model()

    # Вывод информации о модели
    info = model.get_model_info()
    print("\n=== Информация о модели ===")
    print(f"Тип модели: {info['model_type']}")
    print(f"Количество признаков: {info['feature_count']}")
    print(f"MAE: {info['metrics'].get('mae', 'N/A'):.3f} дней")
    print(f"Точность ±2 дня: {info['metrics'].get('accuracy_pm2', 'N/A'):.1%}")
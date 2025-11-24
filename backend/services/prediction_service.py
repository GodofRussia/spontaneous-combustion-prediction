"""
Prediction service for handling ML inference and business logic.
"""

import pandas as pd
import numpy as np
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from pathlib import Path
import uuid

from backend.ml.model_inference import FirePredictionModel
from backend.ml import data_processing
from backend.api.models import PilePrediction
from backend.config import settings

logger = logging.getLogger(__name__)


class PredictionService:
    """Service for handling predictions."""

    def __init__(self):
        """Initialize prediction service."""
        self.model: Optional[FirePredictionModel] = None
        self._load_model()

    def _load_model(self) -> None:
        """Load the ML model."""
        try:
            logger.info(f"Loading model from {settings.MODEL_PATH}")
            self.model = FirePredictionModel(model_path=settings.MODEL_PATH)
            logger.info("Model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise

    def is_model_loaded(self) -> bool:
        """Check if model is loaded."""
        return self.model is not None

    def get_model_info(self) -> Dict[str, Any]:
        """Get model information."""
        if not self.model:
            raise RuntimeError("Model not loaded")
        return self.model.get_model_info()

    def _calculate_risk_level(self, days_to_fire: int) -> str:
        """
        Calculate risk level based on days to fire.

        Args:
            days_to_fire: Number of days until predicted fire

        Returns:
            Risk level: critical, high, medium, or low
        """
        if days_to_fire <= settings.RISK_CRITICAL_THRESHOLD:
            return "critical"
        elif days_to_fire <= settings.RISK_HIGH_THRESHOLD:
            return "high"
        elif days_to_fire <= settings.RISK_MEDIUM_THRESHOLD:
            return "medium"
        else:
            return "low"

    def _calculate_confidence(self, days_to_fire: float, features: Dict[str, Any]) -> str:
        """
        Calculate confidence level for prediction.

        Args:
            days_to_fire: Predicted days to fire
            features: Feature values used for prediction

        Returns:
            Confidence level: high, medium, or low
        """
        # Simple confidence calculation based on prediction range
        if 0 <= days_to_fire <= 14:
            return "high"
        elif 14 < days_to_fire <= 21:
            return "medium"
        else:
            return "low"

    def _extract_features(self, row: pd.Series) -> Dict[str, float]:
        """
        Extract key features from a data row.

        Args:
            row: Data row

        Returns:
            Dictionary of key features
        """
        features = {}

        # Extract available features
        feature_keys = [
            'stock_tons', 'temp_max_mean', 'temp_air_mean',
            'humidity_mean', 'precip_sum', 'wind_avg_mean'
        ]

        for key in feature_keys:
            if key in row.index:
                value = row[key]
                features[key] = float(value) if pd.notna(value) else 0.0

        return features

    def predict_from_dataframe(
        self,
        data: pd.DataFrame,
        horizon_days: int = 3
    ) -> List[PilePrediction]:
        """
        Generate predictions from a DataFrame.

        Args:
            data: Processed DataFrame with features
            horizon_days: Forecast horizon in days

        Returns:
            List of pile predictions
        """
        if not self.model:
            raise RuntimeError("Model not loaded")

        logger.info(f"Generating predictions for {len(data)} observations")

        # Get predictions from model
        result_df = self.model.predict_fire_dates(data, date_col="date")

        # Merge with original data to get additional info
        result_df = result_df.merge(
            data[['pile_id', 'stockyard', 'coal_grade']].drop_duplicates(subset=['pile_id']),
            on='pile_id',
            how='left'
        )

        # Create prediction objects
        predictions = []
        for idx, row in result_df.iterrows():
            # Get original data row for features
            orig_row = data[data['pile_id'] == row['pile_id']].iloc[-1]

            # Extract features
            features = self._extract_features(orig_row)

            # Calculate risk and confidence
            days_rounded = int(row['predicted_days_to_fire_rounded'])
            risk_level = self._calculate_risk_level(days_rounded)
            confidence = self._calculate_confidence(row['predicted_days_to_fire'], features)

            prediction = PilePrediction(
                pile_id=int(row['pile_id']),
                stockyard=int(row['stockyard']) if pd.notna(row.get('stockyard')) else None,
                coal_grade=str(row['coal_grade']) if pd.notna(row.get('coal_grade')) else None,
                observation_date=row['observation_date'],
                predicted_fire_date=row['predicted_fire_date'],
                predicted_days_to_fire=float(row['predicted_days_to_fire']),
                predicted_days_to_fire_rounded=days_rounded,
                confidence=confidence,
                risk_level=risk_level,
                features=features
            )
            predictions.append(prediction)

        logger.info(f"Generated {len(predictions)} predictions")
        return predictions

    def predict_from_csv_files(
        self,
        supplies_path: str,
        temperature_path: str,
        weather_paths: List[str],
        horizon_days: int = 3
    ) -> tuple[List[PilePrediction], Dict[str, Any]]:
        """
        Generate predictions from CSV files.

        Args:
            supplies_path: Path to supplies CSV
            temperature_path: Path to temperature CSV
            weather_paths: List of paths to weather CSV files
            horizon_days: Forecast horizon in days

        Returns:
            Tuple of (List of pile predictions, metadata dict with date range info)
        """
        logger.info("Processing CSV files for prediction")

        # Load data from individual files
        supplies_df = pd.read_csv(supplies_path)
        temperature_df = pd.read_csv(temperature_path)
        weather_list = [pd.read_csv(f) for f in weather_paths]
        weather_df = pd.concat(weather_list, ignore_index=True)
        # Create empty fires df to satisfy the function signatures
        fires_df = pd.DataFrame(columns=["Груз", "Склад", "Дата начала", "Дата оконч.", "Нач.форм.штабеля", "Штабель"])

        # Process data using functions from data_processing
        fires, temp, supp, weather = data_processing.rename_columns(fires_df, temperature_df, supplies_df, weather_df)
        fires, temp, supp, weather = data_processing.parse_dates(fires, temp, supp, weather)

        temp_daily = data_processing.build_temperature_daily(temp)
        supplies_daily = data_processing.build_supplies_daily(supp)
        weather_daily = data_processing.build_weather_daily(weather)

        base = temp_daily.merge(supplies_daily, on=["pile_id", "date"], how="left")
        base = base.merge(weather_daily, on="date", how="left")

        processed_data = data_processing.add_fire_labels(base, fires, horizon_days=horizon_days)
        processed_data = data_processing.add_stockyard_from_supplies(processed_data, supp)

        # Sort by pile and date
        processed_data = processed_data.sort_values(["pile_id", "date"]).reset_index(drop=True)

        # Extract date range information
        date_range_info = self._extract_date_range_info(processed_data, weather)

        # Generate predictions
        predictions = self.predict_from_dataframe(processed_data, horizon_days)

        return predictions, date_range_info

    def _extract_date_range_info(self, processed_data: pd.DataFrame, weather_df: pd.DataFrame) -> Dict[str, Any]:
        """
        Extract date range information from the data.

        Args:
            processed_data: Processed DataFrame with all features
            weather_df: Weather DataFrame with date column

        Returns:
            Dictionary with date range information
        """
        date_info = {}

        def safe_isoformat(dt):
            if pd.notna(dt):
                if hasattr(dt, 'isoformat'):
                    return dt.isoformat()
                return str(dt)
            return None

        # Get date range from processed data
        if 'date' in processed_data.columns and not processed_data['date'].empty:
            min_date = processed_data['date'].min()
            max_date = processed_data['date'].max()

            date_info['data_start_date'] = safe_isoformat(min_date)
            date_info['data_end_date'] = safe_isoformat(max_date)

            if pd.notna(min_date) and pd.notna(max_date):
                if hasattr(min_date, 'year') and hasattr(max_date, 'year'):
                    date_info['data_years'] = list(range(min_date.year, max_date.year + 1))


        # Get weather file date ranges and determine primary year range from it
        if 'date' in weather_df.columns and not weather_df['date'].empty:
            weather_min = weather_df['date'].min()
            weather_max = weather_df['date'].max()

            date_info['weather_start_date'] = safe_isoformat(weather_min)
            date_info['weather_end_date'] = safe_isoformat(weather_max)

            # Extract years from the full weather data range
            if pd.notna(weather_min) and pd.notna(weather_max):
                if hasattr(weather_min, 'year') and hasattr(weather_max, 'year'):
                    weather_years = list(range(weather_min.year, weather_max.year + 1))
                    date_info['years'] = weather_years
                    date_info['weather_years'] = weather_years
                    date_info['primary_year'] = weather_max.year

        logger.info(f"Extracted date range: {date_info}")
        return date_info

    def calculate_metrics(
        self,
        predictions: List[PilePrediction],
        reference_data: pd.DataFrame
    ) -> Dict[str, Any]:
        """
        Calculate evaluation metrics against reference data.

        Args:
            predictions: List of predictions
            reference_data: DataFrame with actual fire dates

        Returns:
            Dictionary with metrics
        """
        logger.info("Calculating evaluation metrics")

        # Convert predictions to DataFrame
        pred_df = pd.DataFrame([
            {
                'pile_id': p.pile_id,
                'predicted_fire_date': p.predicted_fire_date,
                'predicted_days_to_fire': p.predicted_days_to_fire_rounded
            }
            for p in predictions
        ])

        # Merge with reference data
        merged = pred_df.merge(
            reference_data[['pile_id', 'fire_start', 'days_to_fire']],
            on='pile_id',
            how='inner'
        )

        if len(merged) == 0:
            logger.warning("No matching predictions found in reference data")
            return {
                'mae': 0.0,
                'accuracy_pm1': 0.0,
                'accuracy_pm2': 0.0,
                'accuracy_pm3': 0.0,
                'total_predictions': 0,
                'correct_pm2': 0
            }

        # Calculate errors
        errors = np.abs(merged['predicted_days_to_fire'] - merged['days_to_fire'])

        # Calculate metrics
        mae = float(np.mean(errors))
        accuracy_pm1 = float(np.mean(errors <= 1))
        accuracy_pm2 = float(np.mean(errors <= 2))
        accuracy_pm3 = float(np.mean(errors <= 3))

        metrics = {
            'mae': mae,
            'accuracy_pm1': accuracy_pm1,
            'accuracy_pm2': accuracy_pm2,
            'accuracy_pm3': accuracy_pm3,
            'total_predictions': len(merged),
            'correct_pm2': int(np.sum(errors <= 2))
        }

        logger.info(f"Metrics calculated: MAE={mae:.3f}, Accuracy±2={accuracy_pm2:.1%}")
        return metrics

    def evaluate_predictions(
        self,
        predictions_df: pd.DataFrame,
        fires_df: pd.DataFrame
    ) -> Dict[str, Any]:
        """
        Compare predictions with real fire data.

        ВАЖНО: Эта функция НЕ используется для оценки точности модели!
        Она только для визуализации сравнения текущих прогнозов с историческими возгораниями.

        Для правильной оценки точности нужно:
        1. Для каждого реального возгорания найти последнее наблюдение ДО него
        2. Сделать прогноз на основе этого наблюдения
        3. Сравнить с реальной датой

        Текущая реализация просто показывает, какие штабели горели в прошлом.

        Args:
            predictions_df: DataFrame with predictions (pile_id, predicted_fire_date, observation_date)
            fires_df: DataFrame with real fires (Штабель, Дата начала)

        Returns:
            Dictionary with matched predictions for visualization
        """
        logger.info("Comparing current predictions with historical fire data")
        logger.info(f"Fires columns: {fires_df.columns.tolist()}")
        logger.info(f"Fires shape: {fires_df.shape}")

        # Переименовываем только нужные колонки
        fires_renamed = fires_df.rename(columns={
            "Штабель": "pile_id",
            "Дата начала": "fire_start"
        })

        # Преобразуем fire_start в datetime
        fires_renamed['fire_start'] = pd.to_datetime(fires_renamed['fire_start'])

        # Берем только первое возгорание для каждого штабеля
        fires_first = fires_renamed.sort_values('fire_start').groupby('pile_id').first().reset_index()

        logger.info(f"Unique piles with fires: {len(fires_first)}")

        # Merge predictions with fires by pile_id
        merged = predictions_df.merge(
            fires_first[['pile_id', 'fire_start']],
            on='pile_id',
            how='inner'
        )

        if len(merged) == 0:
            logger.warning("No matching predictions found in fire data")
            return {
                'matched_predictions': [],
                'metrics': {
                    'mae': 0.0,
                    'accuracy_pm1': 0.0,
                    'accuracy_pm2': 0.0,
                    'accuracy_pm3': 0.0,
                    'total_matches': 0
                },
                'comparison_data': []
            }

        # Calculate difference in days
        merged['predicted_fire_date'] = pd.to_datetime(merged['predicted_fire_date'])
        merged['observation_date'] = pd.to_datetime(merged.get('observation_date', merged['predicted_fire_date']))

        # Проверяем, был ли прогноз сделан ДО реального возгорания
        merged['prediction_before_fire'] = merged['observation_date'] < merged['fire_start']

        merged['days_difference'] = (merged['fire_start'] - merged['predicted_fire_date']).dt.days
        merged['abs_days_difference'] = merged['days_difference'].abs()

        # Фильтруем только те прогнозы, которые были сделаны ДО возгорания
        valid_predictions = merged[merged['prediction_before_fire']].copy()

        if len(valid_predictions) == 0:
            logger.warning("No valid predictions (all predictions were made AFTER real fires)")
            return {
                'matched_predictions': [],
                'metrics': {
                    'mae': 0.0,
                    'accuracy_pm1': 0.0,
                    'accuracy_pm2': 0.0,
                    'accuracy_pm3': 0.0,
                    'total_matches': 0,
                    'note': 'Все прогнозы сделаны ПОСЛЕ реальных возгораний'
                },
                'comparison_data': []
            }

        # Calculate metrics only for valid predictions
        mae = float(valid_predictions['abs_days_difference'].mean())
        accuracy_pm1 = float((valid_predictions['abs_days_difference'] <= 1).mean())
        accuracy_pm2 = float((valid_predictions['abs_days_difference'] <= 2).mean())
        accuracy_pm3 = float((valid_predictions['abs_days_difference'] <= 3).mean())

        # Prepare matched predictions
        matched_predictions = []
        for _, row in valid_predictions.iterrows():
            matched_predictions.append({
                'pile_id': int(row['pile_id']),
                'observation_date': row['observation_date'].isoformat(),
                'predicted_fire_date': row['predicted_fire_date'].isoformat(),
                'real_fire_date': row['fire_start'].isoformat(),
                'days_difference': int(row['days_difference']),
                'abs_days_difference': int(row['abs_days_difference']),
                'is_match': row['abs_days_difference'] <= 2
            })

        metrics = {
            'mae': mae,
            'accuracy_pm1': accuracy_pm1,
            'accuracy_pm2': accuracy_pm2,
            'accuracy_pm3': accuracy_pm3,
            'total_matches': len(valid_predictions),
            'correct_pm2': int((valid_predictions['abs_days_difference'] <= 2).sum()),
            'invalid_predictions': len(merged) - len(valid_predictions)
        }

        logger.info(f"Evaluation complete: {len(matched_predictions)} valid matches, "
                   f"{len(merged) - len(valid_predictions)} invalid (after fire), "
                   f"MAE={mae:.2f} days")

        return {
            'matched_predictions': matched_predictions,
            'metrics': metrics,
            'comparison_data': matched_predictions
        }


# Global service instance
_prediction_service: Optional[PredictionService] = None


def get_prediction_service() -> PredictionService:
    """Get or create prediction service instance."""
    global _prediction_service
    if _prediction_service is None:
        _prediction_service = PredictionService()
    return _prediction_service
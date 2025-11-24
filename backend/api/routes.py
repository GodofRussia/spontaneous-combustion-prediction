"""
API routes for the FastAPI application.
"""

import logging
from fastapi import APIRouter, UploadFile, File, HTTPException, status
from fastapi.responses import JSONResponse
from datetime import datetime
from typing import List
import uuid
import pandas as pd
from pathlib import Path

from backend.api.models import (
    PredictionRequest,
    PredictionResponse,
    FileUploadResponse,
    MetricsRequest,
    MetricsResponse,
    ModelInfoResponse,
    HealthResponse,
    ErrorResponse
)
from backend.services.prediction_service import get_prediction_service
from backend.config import settings

logger = logging.getLogger(__name__)

# Create router
router = APIRouter()


@router.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """
    Health check endpoint.

    Returns service status and model availability.
    """
    service = get_prediction_service()

    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow(),
        model_loaded=service.is_model_loaded(),
        version=settings.VERSION
    )


@router.get("/model/info", response_model=ModelInfoResponse, tags=["Model"])
async def get_model_info():
    """
    Get information about the loaded ML model.

    Returns model type, features, and training metrics.
    """
    try:
        service = get_prediction_service()
        info = service.get_model_info()

        return ModelInfoResponse(
            model_type=info['model_type'],
            feature_count=info['feature_count'],
            numeric_features=info['numeric_features'],
            categorical_features=info['categorical_features'],
            metrics=info['metrics'],
            model_path=info['model_path']
        )
    except Exception as e:
        logger.error(f"Error getting model info: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get model info: {str(e)}"
        )


@router.post("/upload/csv", response_model=FileUploadResponse, tags=["Upload"])
async def upload_csv_file(
    file: UploadFile = File(...),
    file_type: str = "data"
):
    """
    Upload a CSV file for processing.

    Args:
        file: CSV file to upload
        file_type: Type of file (supplies, temperature, weather, fires)

    Returns:
        Upload confirmation with validation results
    """
    # Validate file extension
    if not file.filename.endswith('.csv'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only CSV files are allowed"
        )

    # Generate upload ID
    upload_id = str(uuid.uuid4())

    try:
        # Save file
        upload_dir = Path(settings.UPLOAD_DIR)
        upload_dir.mkdir(parents=True, exist_ok=True)

        file_path = upload_dir / f"{upload_id}_{file_type}_{file.filename}"

        # Read and save file
        content = await file.read()
        with open(file_path, 'wb') as f:
            f.write(content)

        # Validate CSV
        df = pd.read_csv(file_path)
        row_count = len(df)

        logger.info(f"File uploaded: {file.filename} ({row_count} rows)")

        return FileUploadResponse(
            upload_id=upload_id,
            file_type=file_type,
            filename=file.filename,
            row_count=row_count,
            validation_status="success",
            errors=[],
            warnings=[],
            uploaded_at=datetime.utcnow()
        )

    except pd.errors.EmptyDataError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty"
        )
    except Exception as e:
        logger.error(f"Error uploading file: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload file: {str(e)}"
        )


@router.post("/predict", response_model=PredictionResponse, tags=["Prediction"])
async def create_prediction(request: PredictionRequest):
    """
    Generate fire predictions for all piles.

    This endpoint requires that data files have been uploaded first.
    It processes the data and generates predictions using the ML model.

    Args:
        request: Prediction request with horizon_days parameter

    Returns:
        Prediction results with fire dates and risk levels
    """
    start_time = datetime.utcnow()
    prediction_id = str(uuid.uuid4())

    try:
        service = get_prediction_service()

        # For demo purposes, we'll look for uploaded files
        upload_dir = Path(settings.UPLOAD_DIR)

        # Find most recent uploaded files
        supplies_files = list(upload_dir.glob("*_supplies_*.csv"))
        temperature_files = list(upload_dir.glob("*_temperature_*.csv"))
        weather_files = list(upload_dir.glob("*_weather_*.csv"))

        if not supplies_files or not temperature_files:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Required data files not found. Please upload supplies and temperature data first."
            )

        # Use most recent files
        supplies_path = str(max(supplies_files, key=lambda p: p.stat().st_mtime))
        temperature_path = str(max(temperature_files, key=lambda p: p.stat().st_mtime))
        weather_paths = [str(p) for p in weather_files]

        logger.info(f"Generating predictions with horizon={request.horizon_days} days")

        # Generate predictions
        predictions, date_range_info = service.predict_from_csv_files(
            supplies_path=supplies_path,
            temperature_path=temperature_path,
            weather_paths=weather_paths if weather_paths else [],
            horizon_days=request.horizon_days
        )

        # Calculate statistics
        high_risk_count = sum(
            1 for p in predictions
            if p.risk_level in ['high', 'critical']
        )
        critical_risk_count = sum(
            1 for p in predictions
            if p.risk_level == 'critical'
        )

        # Calculate processing time
        processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000

        return PredictionResponse(
            prediction_id=prediction_id,
            status="completed",
            predictions=predictions,
            total_piles=len(predictions),
            high_risk_count=high_risk_count,
            critical_risk_count=critical_risk_count,
            created_at=start_time,
            processing_time_ms=processing_time,
            date_range=date_range_info
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating predictions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate predictions: {str(e)}"
        )


@router.post("/evaluate", response_model=MetricsResponse, tags=["Evaluation"])
async def evaluate_predictions(request: MetricsRequest):
    """
    Простое сравнение текущих прогнозов с реальными возгораниями из fires.csv.

    Берет все прогнозы и сравнивает с реальными датами возгораний по pile_id.

    Args:
        request: Evaluation request

    Returns:
        Evaluation metrics and matched predictions
    """
    evaluation_id = str(uuid.uuid4())

    try:
        service = get_prediction_service()
        upload_dir = Path(settings.UPLOAD_DIR)

        # Load fires.csv
        fires_path = None
        fires_files = sorted(upload_dir.glob("*_fires_*.csv"), key=lambda p: p.stat().st_mtime, reverse=True)

        if request.reference_data_path:
            fires_path = request.reference_data_path
        elif fires_files:
            fires_path = str(fires_files[0])
        else:
            default_fires_path = Path(settings.DATA_DIR) / "fires.csv"
            if default_fires_path.exists():
                fires_path = str(default_fires_path)

        if not fires_path or not Path(fires_path).exists():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Файл fires.csv не найден"
            )

        fires_df = pd.read_csv(fires_path)

        # Переименовываем колонки
        fires_df = fires_df.rename(columns={
            "Штабель": "pile_id",
            "Дата начала": "fire_start"
        })
        fires_df['fire_start'] = pd.to_datetime(fires_df['fire_start'])

        # Берем первое возгорание для каждого штабеля
        fires_first = fires_df.sort_values('fire_start').groupby('pile_id').first().reset_index()

        # Загружаем текущие прогнозы
        supplies_files = list(upload_dir.glob("*_supplies_*.csv"))
        temperature_files = list(upload_dir.glob("*_temperature_*.csv"))
        weather_files = list(upload_dir.glob("*_weather_*.csv"))

        if not supplies_files or not temperature_files:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Файлы данных не найдены"
            )

        supplies_path = str(max(supplies_files, key=lambda p: p.stat().st_mtime))
        temperature_path = str(max(temperature_files, key=lambda p: p.stat().st_mtime))
        weather_paths = [str(p) for p in weather_files]

        # Генерируем прогнозы
        predictions, _ = service.predict_from_csv_files(
            supplies_path=supplies_path,
            temperature_path=temperature_path,
            weather_paths=weather_paths,
            horizon_days=30
        )

        # Сравниваем прогнозы с реальными возгораниями
        matched_predictions = []
        total_diff = 0
        correct_pm1 = 0
        correct_pm2 = 0
        correct_pm3 = 0

        for pred in predictions:
            fire_row = fires_first[fires_first['pile_id'] == pred.pile_id]
            if len(fire_row) > 0:
                real_fire_date = fire_row.iloc[0]['fire_start']

                # Конвертируем predicted_fire_date в datetime если это строка
                if isinstance(pred.predicted_fire_date, str):
                    pred_date = pd.to_datetime(pred.predicted_fire_date)
                    pred_fire_date_str = pred.predicted_fire_date
                else:
                    pred_date = pred.predicted_fire_date
                    pred_fire_date_str = pred_date.isoformat()

                # Конвертируем observation_date в строку если это не строка
                if isinstance(pred.observation_date, str):
                    obs_date_str = pred.observation_date
                else:
                    obs_date_str = pred.observation_date.isoformat()

                days_diff = (real_fire_date - pred_date).days
                abs_diff = abs(days_diff)

                total_diff += abs_diff
                if abs_diff <= 1:
                    correct_pm1 += 1
                if abs_diff <= 2:
                    correct_pm2 += 1
                if abs_diff <= 3:
                    correct_pm3 += 1

                matched_predictions.append({
                    'pile_id': pred.pile_id,
                    'observation_date': obs_date_str,
                    'predicted_fire_date': pred_fire_date_str,
                    'real_fire_date': real_fire_date.isoformat(),
                    'days_difference': int(days_diff),
                    'abs_days_difference': int(abs_diff),
                    'is_match': abs_diff <= 2,
                    'stockyard': pred.stockyard,
                    'coal_grade': pred.coal_grade
                })

        total_matches = len(matched_predictions)
        mae = total_diff / total_matches if total_matches > 0 else 0.0
        accuracy_pm1 = correct_pm1 / total_matches if total_matches > 0 else 0.0
        accuracy_pm2 = correct_pm2 / total_matches if total_matches > 0 else 0.0
        accuracy_pm3 = correct_pm3 / total_matches if total_matches > 0 else 0.0

        logger.info(f"Evaluation: {total_matches} matches, MAE={mae:.2f}, Accuracy±2={accuracy_pm2:.1%}")

        return MetricsResponse(
            evaluation_id=evaluation_id,
            mae=mae,
            rmse=None,
            accuracy_pm1=accuracy_pm1,
            accuracy_pm2=accuracy_pm2,
            accuracy_pm3=accuracy_pm3,
            total_predictions=total_matches,
            correct_pm2=correct_pm2,
            evaluated_at=datetime.utcnow(),
            matched_predictions=matched_predictions
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error evaluating predictions: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to evaluate predictions: {str(e)}"
        )
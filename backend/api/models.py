"""
Pydantic models for API request/response validation.
"""

from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Optional, List, Dict, Any


class PredictionRequest(BaseModel):
    """Request model for prediction endpoint."""
    horizon_days: int = Field(
        default=3,
        ge=1,
        le=30,
        description="Number of days to forecast ahead"
    )


class PilePrediction(BaseModel):
    """Model for a single pile prediction."""
    pile_id: int = Field(description="Pile identifier")
    stockyard: Optional[int] = Field(None, description="Stockyard number")
    coal_grade: Optional[str] = Field(None, description="Coal grade/type")
    observation_date: datetime = Field(description="Date of observation")
    predicted_fire_date: datetime = Field(description="Predicted fire date")
    predicted_days_to_fire: float = Field(description="Predicted days until fire (raw)")
    predicted_days_to_fire_rounded: int = Field(description="Predicted days until fire (rounded)")
    confidence: str = Field(description="Confidence level: high, medium, low")
    risk_level: str = Field(description="Risk level: critical, high, medium, low")
    features: Optional[Dict[str, float]] = Field(None, description="Key feature values")


class PredictionResponse(BaseModel):
    """Response model for prediction endpoint."""
    prediction_id: str = Field(description="Unique prediction identifier")
    status: str = Field(description="Prediction status")
    predictions: List[PilePrediction] = Field(description="List of predictions")
    total_piles: int = Field(description="Total number of piles")
    high_risk_count: int = Field(description="Number of high/critical risk piles")
    critical_risk_count: int = Field(description="Number of critical risk piles")
    created_at: datetime = Field(description="Prediction creation timestamp")
    processing_time_ms: Optional[float] = Field(None, description="Processing time in milliseconds")
    date_range: Optional[Dict[str, Any]] = Field(None, description="Date range information from data")


class FileUploadResponse(BaseModel):
    """Response model for file upload."""
    upload_id: str = Field(description="Unique upload identifier")
    file_type: str = Field(description="Type of uploaded file")
    filename: str = Field(description="Original filename")
    row_count: int = Field(description="Number of rows in file")
    validation_status: str = Field(description="Validation status: success, warning, error")
    errors: List[str] = Field(default_factory=list, description="Validation errors")
    warnings: List[str] = Field(default_factory=list, description="Validation warnings")
    uploaded_at: datetime = Field(description="Upload timestamp")


class MetricsRequest(BaseModel):
    """Request model for metrics evaluation."""
    prediction_id: str = Field(description="Prediction ID to evaluate")
    reference_data_path: Optional[str] = Field(None, description="Path to reference fires data")


class MatchedPrediction(BaseModel):
    """Model for a matched prediction with real fire data."""
    pile_id: int = Field(description="Pile identifier")
    predicted_fire_date: str = Field(description="Predicted fire date (ISO format)")
    real_fire_date: str = Field(description="Real fire date (ISO format)")
    days_difference: int = Field(description="Difference in days (real - predicted)")
    abs_days_difference: int = Field(description="Absolute difference in days")
    is_match: bool = Field(description="Whether prediction is within ±2 days")
    stockyard: Optional[int] = Field(None, description="Stockyard number")
    coal_grade: Optional[str] = Field(None, description="Coal grade/type")


class MetricsResponse(BaseModel):
    """Response model for metrics evaluation."""
    evaluation_id: str = Field(description="Unique evaluation identifier")
    mae: float = Field(description="Mean Absolute Error in days")
    rmse: Optional[float] = Field(None, description="Root Mean Squared Error")
    accuracy_pm1: float = Field(description="Accuracy within ±1 day")
    accuracy_pm2: float = Field(description="Accuracy within ±2 days")
    accuracy_pm3: float = Field(description="Accuracy within ±3 days")
    total_predictions: int = Field(description="Total number of predictions")
    correct_pm2: int = Field(description="Number of correct predictions within ±2 days")
    evaluated_at: datetime = Field(description="Evaluation timestamp")
    matched_predictions: Optional[List[MatchedPrediction]] = Field(None, description="List of matched predictions")


class ModelInfoResponse(BaseModel):
    """Response model for model information."""
    model_type: str = Field(description="Type of ML model")
    feature_count: int = Field(description="Number of features")
    numeric_features: List[str] = Field(description="List of numeric feature names")
    categorical_features: List[str] = Field(description="List of categorical feature names")
    metrics: Dict[str, Any] = Field(description="Model training metrics")
    model_path: str = Field(description="Path to model file")


class HealthResponse(BaseModel):
    """Response model for health check."""
    status: str = Field(description="Service status")
    timestamp: datetime = Field(description="Current timestamp")
    model_loaded: bool = Field(description="Whether ML model is loaded")
    version: str = Field(description="API version")


class ErrorResponse(BaseModel):
    """Response model for errors."""
    error: str = Field(description="Error type")
    message: str = Field(description="Error message")
    details: Optional[Any] = Field(None, description="Additional error details")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error timestamp")
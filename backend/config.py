"""
Configuration settings for the FastAPI backend application.
"""

from pydantic_settings import BaseSettings
from typing import List
from pathlib import Path

# Определяем корневую директорию проекта
# BASE_DIR will be .../hakaton/
BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    """Application settings."""

    # API Configuration
    API_V1_PREFIX: str = "/api"
    PROJECT_NAME: str = "Coal Fire Prediction API"
    VERSION: str = "1.0.0"
    DEBUG: bool = True

    # CORS Configuration
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173"
    ]

    # File Upload Configuration
    MAX_UPLOAD_SIZE: int = 50 * 1024 * 1024  # 50MB
    UPLOAD_DIR: str = str(BASE_DIR / "data/uploads")
    ALLOWED_EXTENSIONS: List[str] = [".csv"]

    # ML Model Configuration
    MODEL_PATH: str = str(BASE_DIR / "models/fire_prediction_model.pkl")

    # Prediction Configuration
    DEFAULT_HORIZON_DAYS: int = 3
    MAX_HORIZON_DAYS: int = 30
    MIN_HORIZON_DAYS: int = 1

    # Risk Level Thresholds (days)
    RISK_CRITICAL_THRESHOLD: int = 2
    RISK_HIGH_THRESHOLD: int = 7
    RISK_MEDIUM_THRESHOLD: int = 14

    # Logging
    LOG_LEVEL: str = "INFO"

    class Config:
        env_file = ".env"
        case_sensitive = True


# Create global settings instance
settings = Settings()

# Ensure upload directory exists
Path(settings.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
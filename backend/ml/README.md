# ML модуль для предсказания возгораний угля

## Структура

```
backend/ml/
├── __init__.py              # Инициализация модуля
├── data_processing.py       # Функции обработки данных
├── train_model.py          # Скрипт обучения модели
├── model_inference.py      # Загрузка модели и предсказания
└── README.md               # Документация
```

## Обучение модели

```bash
cd backend/ml
python train_model.py
```

Скрипт:
1. Загружает данные из `data/`
2. Обрабатывает и агрегирует данные по дням
3. Обучает XGBoost с GridSearchCV
4. Сохраняет модель в `models/fire_prediction_model.pkl`

## Использование модели

### Загрузка модели

```python
from backend.ml.model_inference import load_model

model = load_model("models/fire_prediction_model.pkl")
```

### Предсказание для новых данных

```python
import pandas as pd
from datetime import datetime

# Подготовка данных
data = pd.DataFrame({
    "pile_id": ["pile_001"],
    "date": [datetime.now()],
    "temp_max_mean": [45.0],
    "temp_max_min": [30.0],
    "temp_max_max": [60.0],
    # ... остальные признаки
})

# Предсказание дат возгорания
predictions = model.predict_fire_dates(data)
print(predictions)
```

### Предсказание для одного наблюдения

```python
observation = {
    "temp_max_mean": 45.0,
    "temp_max_min": 30.0,
    "temp_max_max": 60.0,
    "coal_grade": "ДГ",
    "stockyard": "Склад 1",
    # ... остальные признаки
}

result = model.predict_single_observation(
    observation=observation,
    observation_date=datetime.now()
)

print(f"Предсказанная дата возгорания: {result['predicted_fire_date']}")
print(f"Дней до возгорания: {result['predicted_days_to_fire_rounded']}")
```

### Информация о модели

```python
info = model.get_model_info()
print(f"MAE: {info['metrics']['mae']:.3f} дней")
print(f"Точность ±2 дня: {info['metrics']['accuracy_pm2']:.1%}")
```

## Интеграция с FastAPI

```python
from fastapi import FastAPI
from backend.ml.model_inference import load_model

app = FastAPI()
model = load_model()

@app.post("/predict")
async def predict(data: dict):
    result = model.predict_single_observation(
        observation=data["features"],
        observation_date=data["date"]
    )
    return result
```

## Требования

- pandas
- numpy
- scikit-learn
- xgboost
- pickle (встроен в Python)

## Метрики модели

- **MAE**: Средняя абсолютная ошибка в днях
- **Accuracy ±2 дня**: Доля предсказаний с точностью ±2 дня (требуется ≥70%)
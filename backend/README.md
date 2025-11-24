# Coal Fire Prediction API - Backend

FastAPI приложение для предсказания самовозгорания угля в штабелях.

## Структура проекта

```
backend/
├── __init__.py
├── main.py                          # Точка входа FastAPI приложения
├── config.py                        # Настройки конфигурации
├── requirements.txt                 # Python зависимости
├── api/
│   ├── __init__.py
│   ├── models.py                    # Pydantic модели для валидации
│   └── routes.py                    # API endpoints
├── services/
│   ├── __init__.py
│   └── prediction_service.py        # Бизнес-логика предсказаний
└── ml/
    ├── __init__.py
    ├── model_inference.py           # Загрузка и инференс модели
    ├── data_processing.py           # Обработка данных
    └── train_model.py               # Обучение модели
```

## Установка

### 1. Создайте виртуальное окружение

```bash
cd backend
python -m venv venv

# Активация на Linux/Mac:
source venv/bin/activate

# Активация на Windows:
venv\Scripts\activate
```

### 2. Установите зависимости

```bash
pip install -r requirements.txt
```

### 3. Убедитесь, что модель обучена

Модель должна находиться в `models/fire_prediction_model.pkl`. Если её нет, запустите обучение:

```bash
cd ..
python -m backend.ml.train_model
```

## Запуск сервера

### Режим разработки (с автоперезагрузкой)

```bash
# Из корневой директории проекта
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

### Режим продакшена

```bash
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Альтернативный запуск через Python

```bash
python -m backend.main
```

## API Endpoints

После запуска сервера доступна интерактивная документация:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

### Основные endpoints:

#### 1. Проверка здоровья
```http
GET /api/health
```

Возвращает статус сервиса и информацию о загруженной модели.

#### 2. Информация о модели
```http
GET /api/model/info
```

Возвращает информацию о ML модели: тип, признаки, метрики.

#### 3. Загрузка CSV файлов
```http
POST /api/upload/csv?file_type=supplies
Content-Type: multipart/form-data

file: supplies.csv
```

Параметры:
- `file_type`: тип файла (supplies, temperature, weather, fires)

#### 4. Генерация предсказаний
```http
POST /api/predict
Content-Type: application/json

{
  "horizon_days": 3
}
```

Генерирует предсказания для всех штабелей на основе загруженных данных.

#### 5. Оценка модели
```http
POST /api/evaluate
Content-Type: application/json

{
  "prediction_id": "uuid",
  "reference_data_path": "path/to/fires.csv"
}
```

Оценивает качество предсказаний по референсным данным.

## Примеры использования

### Python (requests)

```python
import requests

# 1. Проверка здоровья
response = requests.get("http://localhost:8000/api/health")
print(response.json())

# 2. Загрузка файла
with open("data/supplies.csv", "rb") as f:
    files = {"file": f}
    response = requests.post(
        "http://localhost:8000/api/upload/csv?file_type=supplies",
        files=files
    )
    print(response.json())

# 3. Генерация предсказаний
response = requests.post(
    "http://localhost:8000/api/predict",
    json={"horizon_days": 3}
)
predictions = response.json()
print(f"Всего штабелей: {predictions['total_piles']}")
print(f"Высокий риск: {predictions['high_risk_count']}")
```

### cURL

```bash
# Проверка здоровья
curl http://localhost:8000/api/health

# Загрузка файла
curl -X POST "http://localhost:8000/api/upload/csv?file_type=supplies" \
  -F "file=@data/supplies.csv"

# Генерация предсказаний
curl -X POST "http://localhost:8000/api/predict" \
  -H "Content-Type: application/json" \
  -d '{"horizon_days": 3}'
```

## Конфигурация

Настройки можно изменить в файле `config.py` или через переменные окружения:

```bash
# Создайте файл .env в директории backend/
API_V1_PREFIX=/api
DEBUG=True
MODEL_PATH=models/fire_prediction_model.pkl
MAX_UPLOAD_SIZE=52428800
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173
```

### Основные настройки:

- `API_V1_PREFIX`: префикс для API endpoints (по умолчанию `/api`)
- `DEBUG`: режим отладки (по умолчанию `True`)
- `MODEL_PATH`: путь к файлу модели
- `MAX_UPLOAD_SIZE`: максимальный размер загружаемого файла (50MB)
- `ALLOWED_ORIGINS`: разрешённые CORS origins для frontend
- `DEFAULT_HORIZON_DAYS`: горизонт прогноза по умолчанию (3 дня)
- `RISK_CRITICAL_THRESHOLD`: порог критического риска (2 дня)
- `RISK_HIGH_THRESHOLD`: порог высокого риска (7 дней)
- `RISK_MEDIUM_THRESHOLD`: порог среднего риска (14 дней)

## Формат данных

### Входные CSV файлы:

1. **supplies.csv** - данные о поставках угля
2. **temperature.csv** - измерения температуры штабелей
3. **weather_data_*.csv** - данные о погоде
4. **fires.csv** (опционально) - референсные данные о возгораниях для оценки

### Формат ответа предсказаний:

```json
{
  "prediction_id": "uuid",
  "status": "completed",
  "predictions": [
    {
      "pile_id": 1,
      "stockyard": 6,
      "coal_grade": "A1",
      "observation_date": "2020-09-30T00:00:00",
      "predicted_fire_date": "2020-10-03T00:00:00",
      "predicted_days_to_fire": 3.2,
      "predicted_days_to_fire_rounded": 3,
      "confidence": "high",
      "risk_level": "high",
      "features": {
        "stock_tons": 1234.5,
        "temp_max_mean": 45.2,
        "temp_air_mean": 18.5
      }
    }
  ],
  "total_piles": 48,
  "high_risk_count": 5,
  "critical_risk_count": 2,
  "created_at": "2024-01-15T10:35:00Z",
  "processing_time_ms": 1250
}
```

### Уровни риска:

- **critical** (критический): 0-2 дня до возгорания
- **high** (высокий): 3-7 дней
- **medium** (средний): 8-14 дней
- **low** (низкий): >14 дней

## Требования к модели

- Точность ≥70% в пределах ±2 дня
- Горизонт прогноза ≥3 дня
- MAE (средняя абсолютная ошибка) ≤2 дня

## Логирование

Логи выводятся в консоль с уровнем INFO. Для изменения уровня логирования:

```python
# В config.py
LOG_LEVEL = "DEBUG"  # или "INFO", "WARNING", "ERROR"
```

## Обработка ошибок

API возвращает структурированные ошибки:

```json
{
  "error": "Validation Error",
  "message": "Invalid request data",
  "details": [...],
  "timestamp": "2024-01-15T10:30:00Z"
}
```

Коды ошибок:
- `400` - Неверный запрос (невалидные данные)
- `404` - Ресурс не найден
- `422` - Ошибка валидации
- `500` - Внутренняя ошибка сервера

## Разработка

### Запуск тестов

```bash
pytest backend/tests/ -v
```

### Форматирование кода

```bash
black backend/
flake8 backend/
```

## Производительность

- Время обработки одного предсказания: ~25-50ms
- Поддержка до 100+ штабелей одновременно
- Рекомендуемая конфигурация: 2 CPU, 4GB RAM

## Troubleshooting

### Модель не загружается

```
FileNotFoundError: Файл модели не найден
```

**Решение**: Убедитесь, что файл `models/fire_prediction_model.pkl` существует. Запустите обучение модели.

### Ошибка при загрузке CSV

```
ValidationError: Missing required columns
```

**Решение**: Проверьте формат CSV файла. Убедитесь, что все необходимые колонки присутствуют.

### CORS ошибки

```
Access-Control-Allow-Origin error
```

**Решение**: Добавьте URL вашего frontend в `ALLOWED_ORIGINS` в `config.py`.

## Лицензия

Внутренний проект для предсказания самовозгорания угля.
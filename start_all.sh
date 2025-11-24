#!/bin/bash

# Скрипт запуска всей системы Coal Fire Prediction
# Использование: ./start_all.sh

set -e

echo "🔥 Coal Fire Prediction System - Полный запуск"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Функция для проверки доступности порта
check_port() {
    if lsof -Pi :$1 -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo "⚠️  Порт $1 уже занят!"
        echo "   Остановите процесс на этом порту или измените порт в конфигурации."
        return 1
    fi
    return 0
}

# Проверка портов
echo "🔍 Проверка доступности портов..."
check_port 8000 || exit 1
check_port 5173 || exit 1
echo "✅ Порты свободны"
echo ""

# Проверка зависимостей
echo "🔍 Проверка системных требований..."

if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 не найден. Установите Python 3.9+"
    exit 1
fi
echo "✅ Python: $(python3 --version)"

if ! command -v node &> /dev/null; then
    echo "❌ Node.js не найден. Установите Node.js 18+"
    exit 1
fi
echo "✅ Node.js: $(node --version)"

if ! command -v npm &> /dev/null; then
    echo "❌ npm не найден"
    exit 1
fi
echo "✅ npm: $(npm --version)"
echo ""

# Создание директории для логов
mkdir -p logs

# Функция очистки при выходе
cleanup() {
    echo ""
    echo "🛑 Остановка всех сервисов..."

    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null || true
        echo "   ✅ Backend остановлен"
    fi

    if [ ! -z "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null || true
        echo "   ✅ Frontend остановлен"
    fi

    echo ""
    echo "👋 Система остановлена"
    exit 0
}

# Установка обработчика сигналов
trap cleanup SIGINT SIGTERM

echo "🚀 Запуск Backend..."
./start_backend.sh > logs/backend.log 2>&1 &
BACKEND_PID=$!
echo "   PID: $BACKEND_PID"
echo "   Логи: logs/backend.log"
echo "   Ожидание запуска backend..."
sleep 5

# Проверка, что backend запустился
if ! kill -0 $BACKEND_PID 2>/dev/null; then
    echo "Backend не запустился. Проверьте logs/backend.log"
    exit 1
fi

# Проверка доступности API
for i in {1..10}; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo "Backend готов"
        break
    fi
    if [ $i -eq 10 ]; then
        echo "Backend не отвечает"
        cleanup
        exit 1
    fi
    sleep 1
done
echo ""

echo "Запуск Frontend..."
./start_frontend.sh > logs/frontend.log 2>&1 &
FRONTEND_PID=$!
echo "   PID: $FRONTEND_PID"
echo "   Логи: logs/frontend.log"
echo "   Ожидание запуска frontend..."
sleep 8

# Проверка, что frontend запустился
if ! kill -0 $FRONTEND_PID 2>/dev/null; then
    echo "Frontend не запустился. Проверьте logs/frontend.log"
    cleanup
    exit 1
fi
echo "   Frontend готов"
echo ""

# Вывод информации
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Система успешно запущена!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📍 Доступные сервисы:"
echo "   🌐 Frontend:        http://localhost:5173"
echo "   🔌 Backend API:     http://localhost:8000"
echo "   📚 API Docs:        http://localhost:8000/docs"
echo ""
echo "📝 Логи:"
echo "   Backend:  logs/backend.log"
echo "   Frontend: logs/frontend.log"
echo ""
echo "Нажмите Ctrl+C для остановки всей системы"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Ожидание сигнала остановки
wait
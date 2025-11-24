#!/bin/bash

# Скрипт запуска React frontend
# Использование: ./start_frontend.sh

set -e

echo "🚀 Запуск Coal Fire Prediction Frontend..."
echo ""

# Проверка Node.js
if ! command -v node &> /dev/null; then
    echo "❌ Node.js не найден. Установите Node.js 18 или выше."
    exit 1
fi

# Проверка npm
if ! command -v npm &> /dev/null; then
    echo "❌ npm не найден. Установите npm."
    exit 1
fi

# Переход в директорию frontend
cd "$(dirname "$0")/frontend"

# Проверка node_modules
if [ ! -d "node_modules" ]; then
    echo "📦 Установка зависимостей..."
    npm install
else
    echo "✅ Зависимости уже установлены"
fi

# Проверка .env файла
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        echo "📝 Создание .env файла из .env.example..."
        cp .env.example .env
    else
        echo "⚠️  Предупреждение: .env файл не найден!"
    fi
fi

# Запуск dev сервера
echo "✅ Запуск Vite dev сервера..."
echo ""
echo "📍 Frontend доступен по адресу: http://localhost:5173"
echo "🔗 Убедитесь, что backend запущен на http://localhost:8000"
echo ""
echo "Нажмите Ctrl+C для остановки сервера"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

npm run dev
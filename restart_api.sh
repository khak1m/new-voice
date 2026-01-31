#!/bin/bash
# Скрипт для обновления и перезапуска API на сервере

set -e

echo "🔄 Обновление кода..."
git pull origin main

echo "🔄 Активация виртуального окружения..."
source venv/bin/activate

echo "📦 Обновление зависимостей (если нужно)..."
# API-only requirements avoid LiveKit Agents resolver conflicts on servers.
pip install -r requirements-api.txt --quiet

echo "🛑 Остановка старого процесса uvicorn..."
pkill -f "uvicorn src.api.main:app" || true
sleep 2

echo "🚀 Запуск API сервера..."
mkdir -p logs
nohup python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000 > logs/api.log 2>&1 &

echo "⏳ Ожидание запуска сервера..."
sleep 3

echo "✅ Проверка статуса..."
if curl -s http://localhost:8000/health > /dev/null; then
    echo "✅ API сервер успешно запущен!"
    echo "📊 Логи: tail -f logs/api.log"
else
    echo "❌ Ошибка запуска API сервера"
    echo "📋 Последние строки лога:"
    tail -20 logs/api.log
    exit 1
fi

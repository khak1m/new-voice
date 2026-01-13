#!/bin/bash
# Скрипт для исправления agent_name и перезапуска агента

echo "=== Исправление Voice Agent ==="

# 1. Останавливаем старый агент
echo "1. Останавливаем старый агент..."
pkill -f simple_agent
sleep 2

# 2. Переходим в директорию проекта
cd /root/new-voice

# 3. Получаем последние изменения из GitHub
echo "2. Получаем обновления из GitHub..."
git pull

# 4. Активируем виртуальное окружение
source venv/bin/activate

# 5. Запускаем агента в фоне
echo "3. Запускаем агента..."
nohup python -m src.voice_agent.simple_agent dev > agent.log 2>&1 &

# Ждём 3 секунды
sleep 3

# 6. Проверяем логи
echo "4. Проверяем agent_name в логах:"
tail -20 agent.log | grep agent_name

echo ""
echo "=== Готово! ==="
echo "Если видите 'agent_name': 'voice-agent' — всё работает!"
echo "Если видите 'agent_name': '' — напишите мне"

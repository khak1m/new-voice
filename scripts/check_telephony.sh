#!/bin/bash

echo "==================================="
echo "Диагностика телефонии NEW-VOICE"
echo "==================================="
echo ""

# Проверка 1: Агент запущен?
echo "1. Проверка Voice Agent..."
if ps aux | grep -q "[s]imple_agent"; then
    echo "   ✅ Voice Agent запущен"
    ps aux | grep "[s]imple_agent" | awk '{print "   PID:", $2, "| Время:", $9, "| Память:", $6/1024 "MB"}'
else
    echo "   ❌ Voice Agent НЕ запущен!"
    echo "   Запустите: python -m src.voice_agent.simple_agent dev"
fi
echo ""

# Проверка 2: Переменные окружения
echo "2. Проверка переменных окружения..."
cd /root/new-voice

if [ -f .env ]; then
    if grep -q "LIVEKIT_URL" .env && grep -q "LIVEKIT_API_KEY" .env; then
        echo "   ✅ LIVEKIT настройки найдены"
    else
        echo "   ❌ LIVEKIT настройки отсутствуют в .env"
    fi
    
    if grep -q "DEEPGRAM_API_KEY" .env; then
        echo "   ✅ DEEPGRAM_API_KEY найден"
    else
        echo "   ❌ DEEPGRAM_API_KEY отсутствует"
    fi
    
    if grep -q "CARTESIA_API_KEY" .env; then
        echo "   ✅ CARTESIA_API_KEY найден"
    else
        echo "   ❌ CARTESIA_API_KEY отсутствует"
    fi
else
    echo "   ❌ Файл .env не найден!"
fi
echo ""

# Проверка 3: Ollama
echo "3. Проверка Ollama..."
if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "   ✅ Ollama работает"
    if curl -s http://localhost:11434/api/tags | grep -q "qwen2:1.5b"; then
        echo "   ✅ Модель qwen2:1.5b загружена"
    else
        echo "   ⚠️  Модель qwen2:1.5b не найдена"
    fi
else
    echo "   ❌ Ollama не отвечает"
fi
echo ""

# Проверка 4: Порты
echo "4. Проверка сетевых подключений..."
if netstat -tuln 2>/dev/null | grep -q ":11434"; then
    echo "   ✅ Ollama порт 11434 открыт"
else
    echo "   ⚠️  Ollama порт 11434 не найден"
fi
echo ""

echo "==================================="
echo "Следующие шаги:"
echo "==================================="
echo "1. Если агент запущен - проверьте его логи"
echo "2. Зайдите в LiveKit Dashboard и проверьте:"
echo "   - SIP Inbound Trunk существует"
echo "   - Dispatch Rule настроен на agent: voice-agent"
echo "3. Позвоните на +7 934 662-08-75"
echo "4. Смотрите логи агента во время звонка"
echo ""

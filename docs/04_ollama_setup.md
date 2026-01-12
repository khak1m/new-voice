# Установка Ollama на сервер

Ollama — это инструмент для запуска LLM локально. Работает без блокировок, бесплатно.

## Требования

- Ubuntu 20.04+ (у нас 24.04 ✅)
- Минимум 8GB RAM для Llama 3.1 8B
- ~5GB места на диске для модели

> ⚠️ У нас сервер с 4GB RAM — это на грани. Можно попробовать модели поменьше (Qwen2 1.5B, Phi-3 mini).

## Шаг 1: Установка Ollama

Подключись к серверу:
```bash
ssh root@77.233.212.58
```

Установи Ollama:
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

## Шаг 2: Запуск Ollama

Ollama автоматически запускается как сервис. Проверь:
```bash
systemctl status ollama
```

Если не запущен:
```bash
systemctl start ollama
systemctl enable ollama
```

## Шаг 3: Скачивание модели

Для сервера с 4GB RAM рекомендую лёгкие модели:

```bash
# Вариант 1: Qwen2 1.5B (самая лёгкая, ~1GB RAM)
ollama pull qwen2:1.5b

# Вариант 2: Phi-3 mini (Microsoft, ~2GB RAM)
ollama pull phi3:mini

# Вариант 3: Llama 3.2 3B (если хватит RAM)
ollama pull llama3.2:3b
```

Если RAM хватает (8GB+):
```bash
# Llama 3.1 8B — лучшее качество
ollama pull llama3.1:8b
```

## Шаг 4: Проверка

Проверь что модель работает:
```bash
ollama run qwen2:1.5b "Привет! Как дела?"
```

## Шаг 5: Открыть порт для внешнего доступа

По умолчанию Ollama слушает только localhost. Чтобы обращаться с других машин:

```bash
# Создай override для systemd
sudo mkdir -p /etc/systemd/system/ollama.service.d

# Добавь конфигурацию
sudo tee /etc/systemd/system/ollama.service.d/override.conf << EOF
[Service]
Environment="OLLAMA_HOST=0.0.0.0:11434"
EOF

# Перезапусти
sudo systemctl daemon-reload
sudo systemctl restart ollama
```

Проверь что слушает на всех интерфейсах:
```bash
ss -tlnp | grep 11434
```

## Шаг 6: Firewall (если включен)

```bash
sudo ufw allow 11434/tcp
```

## Проверка с локальной машины

После настройки проверь с твоего компьютера:
```bash
curl http://77.233.212.58:11434/api/tags
```

Должен вернуть JSON со списком моделей.

---

## Использование в коде

```python
from providers import OllamaLLMProvider

# Подключение к серверу
provider = OllamaLLMProvider(
    host="http://77.233.212.58:11434",
    model="qwen2:1.5b"  # или другая модель
)

# Генерация
response = provider.generate(
    system_prompt="Ты администратор салона красоты",
    messages=[{"role": "user", "content": "Хочу записаться"}]
)
print(response)
```

---

## Рекомендуемые модели по RAM

| RAM | Модель | Качество |
|-----|--------|----------|
| 2GB | qwen2:0.5b | Базовое |
| 4GB | qwen2:1.5b, phi3:mini | Хорошее |
| 8GB | llama3.1:8b, mistral:7b | Отличное |
| 16GB+ | llama3.1:70b | Лучшее |

---

## Troubleshooting

**Ollama не запускается:**
```bash
journalctl -u ollama -f
```

**Модель не помещается в RAM:**
```bash
# Проверь свободную память
free -h

# Попробуй модель поменьше
ollama pull qwen2:0.5b
```

**Медленная генерация:**
- Это нормально для CPU-only сервера
- Для ускорения нужен GPU

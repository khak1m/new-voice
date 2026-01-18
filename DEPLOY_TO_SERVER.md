# 🚀 Деплой на Сервер 77.233.212.58

## Вариант 1: FastAPI раздает фронтенд (Рекомендуется)

Это самый простой способ - один сервер раздает и API, и фронтенд.

### Шаг 1: Соберите фронтенд

На вашем локальном компьютере:

```bash
cd new-voice-frontend
npm run build
```

Это создаст папку `dist/` с собранным фронтендом.

### Шаг 2: Загрузите файлы на сервер

```bash
# Загрузите собранный фронтенд на сервер
scp -r dist/* root@77.233.212.58:/root/new-voice/frontend-dist/

# Или используйте FileZilla/WinSCP для загрузки папки dist
```

### Шаг 3: Обновите main.py на сервере

Подключитесь к серверу:
```bash
ssh root@77.233.212.58
```

Отредактируйте `/root/new-voice/src/api/main.py`:

```python
# В конце файла, ПОСЛЕ всех роутеров, добавьте:

# Раздача фронтенда (должно быть ПОСЛЕДНИМ!)
from fastapi.staticfiles import StaticFiles
from pathlib import Path

frontend_dist = Path(__file__).parent.parent.parent / "frontend-dist"
if frontend_dist.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="frontend")
```

### Шаг 4: Перезапустите бэкенд на сервере

```bash
# Остановите текущий процесс (если запущен)
pkill -f uvicorn

# Запустите заново
cd /root/new-voice
nohup python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000 > logs/api.log 2>&1 &
```

### Шаг 5: Откройте в браузере

```
http://77.233.212.58:8000
```

Готово! Фронтенд и API работают на одном порту.

---

## Вариант 2: Nginx + 2 сервера (Продакшен)

Более профессиональный вариант с Nginx.

### Шаг 1: Установите Nginx на сервере

```bash
ssh root@77.233.212.58
apt update
apt install nginx -y
```

### Шаг 2: Соберите и загрузите фронтенд

```bash
# Локально
cd new-voice-frontend
npm run build

# Загрузите на сервер
scp -r dist/* root@77.233.212.58:/var/www/new-voice/
```

### Шаг 3: Настройте Nginx

На сервере создайте файл `/etc/nginx/sites-available/new-voice`:

```nginx
server {
    listen 80;
    server_name 77.233.212.58;

    # Фронтенд
    location / {
        root /var/www/new-voice;
        try_files $uri $uri/ /index.html;
    }

    # API
    location /api {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    # WebSocket для LiveKit (если нужно)
    location /ws {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

Активируйте конфигурацию:

```bash
ln -s /etc/nginx/sites-available/new-voice /etc/nginx/sites-enabled/
nginx -t
systemctl restart nginx
```

### Шаг 4: Запустите бэкенд

```bash
cd /root/new-voice
nohup python -m uvicorn src.api.main:app --host 127.0.0.1 --port 8000 > logs/api.log 2>&1 &
```

### Шаг 5: Откройте в браузере

```
http://77.233.212.58
```

---

## Вариант 3: Systemd сервисы (Автозапуск)

Для автоматического запуска при перезагрузке сервера.

### Создайте systemd сервис для API

На сервере создайте `/etc/systemd/system/new-voice-api.service`:

```ini
[Unit]
Description=NEW-VOICE API
After=network.target postgresql.service

[Service]
Type=simple
User=root
WorkingDirectory=/root/new-voice
Environment="PATH=/usr/local/bin:/usr/bin:/bin"
ExecStart=/usr/bin/python3 -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Активируйте сервис:

```bash
systemctl daemon-reload
systemctl enable new-voice-api
systemctl start new-voice-api
systemctl status new-voice-api
```

---

## 🔧 Обновление фронтенда

Когда вы вносите изменения в фронтенд:

```bash
# Локально
cd new-voice-frontend
npm run build

# Загрузите на сервер
scp -r dist/* root@77.233.212.58:/root/new-voice/frontend-dist/

# Или для Nginx варианта:
scp -r dist/* root@77.233.212.58:/var/www/new-voice/

# Перезапуск не нужен! Файлы обновятся автоматически
```

---

## 📋 Checklist для деплоя

### Перед деплоем:

- [ ] Фронтенд собран (`npm run build`)
- [ ] Все зависимости установлены на сервере
- [ ] База данных настроена и запущена
- [ ] `.env` файл настроен на сервере
- [ ] Порты открыты (8000 или 80)

### После деплоя:

- [ ] API доступен: `http://77.233.212.58:8000/docs`
- [ ] Фронтенд открывается: `http://77.233.212.58:8000` или `http://77.233.212.58`
- [ ] API запросы работают (проверьте DevTools)
- [ ] База данных подключена
- [ ] Логи без ошибок

---

## 🐛 Troubleshooting

### Проблема: Фронтенд не загружается

**Решение:**
```bash
# Проверьте, что файлы загружены
ls -la /root/new-voice/frontend-dist/

# Проверьте права доступа
chmod -R 755 /root/new-voice/frontend-dist/
```

### Проблема: API не отвечает

**Решение:**
```bash
# Проверьте, что процесс запущен
ps aux | grep uvicorn

# Проверьте логи
tail -f /root/new-voice/logs/api.log

# Перезапустите
pkill -f uvicorn
cd /root/new-voice
nohup python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000 > logs/api.log 2>&1 &
```

### Проблема: 502 Bad Gateway (Nginx)

**Решение:**
```bash
# Проверьте, что бэкенд запущен
curl http://localhost:8000/health

# Проверьте логи Nginx
tail -f /var/log/nginx/error.log

# Перезапустите Nginx
systemctl restart nginx
```

---

## 🎯 Рекомендация

**Для быстрого старта:** Используйте Вариант 1 (FastAPI раздает фронтенд)

**Для продакшена:** Используйте Вариант 2 (Nginx) + Вариант 3 (Systemd)

---

**Дата:** 2026-01-18

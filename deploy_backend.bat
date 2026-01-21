@echo off
REM Скрипт для деплоя backend на сервер (Windows)
REM Использование: deploy_backend.bat

echo.
echo ========================================
echo   Деплой BACKEND на сервер
echo ========================================
echo.

REM Настройки
set SERVER=77.233.212.58
set USER=root
set REMOTE_PATH=/root/new-voice

echo [1/5] Проверка git статуса...
git status

echo.
echo [2/5] Подключение к серверу и обновление кода...
ssh %USER%@%SERVER% "cd %REMOTE_PATH% && git pull origin main"

echo.
echo [3/5] Установка зависимостей на сервере...
ssh %USER%@%SERVER% "cd %REMOTE_PATH% && source venv/bin/activate && pip install -r requirements.txt"

echo.
echo [4/5] Применение миграций базы данных...
ssh %USER%@%SERVER% "cd %REMOTE_PATH% && source venv/bin/activate && python -m alembic upgrade head"

echo.
echo [5/5] Перезапуск API сервиса...
ssh %USER%@%SERVER% "systemctl restart new-voice-api"

echo.
echo ========================================
echo   Проверка статуса сервиса...
echo ========================================
echo.
ssh %USER%@%SERVER% "systemctl status new-voice-api --no-pager"

echo.
echo ========================================
echo   Деплой завершен!
echo ========================================
echo.
echo Backend обновлен на сервере: %SERVER%
echo API доступен: http://%SERVER%:8000
echo Swagger: http://%SERVER%:8000/docs
echo.
echo Проверьте логи: ssh %USER%@%SERVER% "journalctl -u new-voice-api -f"
echo.
pause

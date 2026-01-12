# Этап 1: Настройка сервера

## Требования к серверу

- **ОС:** Ubuntu 22.04 / Debian 12
- **CPU:** минимум 2 ядра
- **RAM:** минимум 4 ГБ
- **Диск:** минимум 30 ГБ
- **Сеть:** публичный IP

## Подключение к серверу

```bash
ssh root@YOUR_SERVER_IP
```

## Автоматическая установка

```bash
# Скачать и запустить скрипт
curl -fsSL https://raw.githubusercontent.com/khak1m/new-voice/main/scripts/setup_server.sh | bash
```

## Ручная установка

### 1. Обновление системы

```bash
apt update && apt upgrade -y
```

### 2. Установка Python 3.11

```bash
apt install -y software-properties-common
add-apt-repository -y ppa:deadsnakes/ppa
apt update
apt install -y python3.11 python3.11-venv python3.11-dev python3-pip
```

### 3. Установка Docker

```bash
curl -fsSL https://get.docker.com | sh
systemctl enable docker
systemctl start docker
```

### 4. Установка Git

```bash
apt install -y git
```

### 5. Настройка файрвола

```bash
ufw allow 22/tcp    # SSH
ufw allow 80/tcp    # HTTP
ufw allow 443/tcp   # HTTPS
ufw allow 7880/tcp  # LiveKit
ufw allow 7881/tcp  # LiveKit
ufw enable
```

## Проверка установки

```bash
python3.11 --version  # Python 3.11.x
docker --version      # Docker 24.x+
git --version         # git 2.x+
```

## Следующий шаг

→ [Регистрация сервисов](02_services_setup.md)

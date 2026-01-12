#!/bin/bash

# NEW-VOICE 2.0 - Server Setup Script
# Для Ubuntu 22.04 / Debian 12

set -e

echo "=========================================="
echo "NEW-VOICE 2.0 - Настройка сервера"
echo "=========================================="

# Обновление системы
echo "[1/5] Обновление системы..."
apt update && apt upgrade -y

# Установка базовых пакетов
echo "[2/5] Установка базовых пакетов..."
apt install -y \
    software-properties-common \
    curl \
    wget \
    git \
    htop \
    nano \
    ufw

# Установка Python 3.11
echo "[3/5] Установка Python 3.11..."
add-apt-repository -y ppa:deadsnakes/ppa
apt update
apt install -y python3.11 python3.11-venv python3.11-dev python3-pip

# Установка Docker
echo "[4/5] Установка Docker..."
curl -fsSL https://get.docker.com | sh
systemctl enable docker
systemctl start docker

# Установка Docker Compose
apt install -y docker-compose-plugin

# Настройка файрвола
echo "[5/5] Настройка файрвола..."
ufw allow 22/tcp      # SSH
ufw allow 80/tcp      # HTTP
ufw allow 443/tcp     # HTTPS
ufw allow 7880/tcp    # LiveKit
ufw allow 7881/tcp    # LiveKit
ufw --force enable

echo "=========================================="
echo "Установка завершена!"
echo "=========================================="
echo ""
echo "Версии:"
python3.11 --version
docker --version
git --version
echo ""
echo "Следующий шаг: регистрация сервисов (см. docs/02_services_setup.md)"

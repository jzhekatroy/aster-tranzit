#!/bin/bash

###############################################################################
# Phone Proxy System - Упрощенная установка (без Asterisk)
# Только веб-интерфейс и API
###############################################################################

set -e  # Остановка при ошибке

echo "======================================"
echo "Phone Proxy System - Упрощенная установка"
echo "Только веб-интерфейс (без Asterisk)"
echo "======================================"
echo ""

# Проверка что скрипт запущен от root
if [ "$EUID" -ne 0 ]; then 
    echo "Пожалуйста, запустите скрипт с sudo"
    exit 1
fi

# Определение директории проекта
PROJECT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
echo "Директория проекта: $PROJECT_DIR"
echo ""

# Обновление системы
echo "1. Обновление системы..."
apt-get update

# Установка Python и зависимостей
echo ""
echo "2. Установка Python и pip..."
apt-get install -y python3 python3-pip python3-venv python3-dev build-essential

# Установка MariaDB
echo ""
echo "3. Установка MariaDB..."
apt-get install -y mariadb-server mariadb-client

# Запуск MariaDB
systemctl start mariadb
systemctl enable mariadb
echo "MariaDB установлена и запущена!"

# Создание виртуального окружения Python
echo ""
echo "4. Создание виртуального окружения Python..."
cd "$PROJECT_DIR"
python3 -m venv venv
source venv/bin/activate

# Установка Python зависимостей
echo ""
echo "5. Установка Python зависимостей..."
pip install --upgrade pip
pip install -r requirements.txt

# Создание .env файла
echo ""
echo "6. Создание конфигурации..."
if [ ! -f .env ]; then
    cp env.example .env
    echo "Создан файл .env."
else
    echo "Файл .env уже существует."
fi

# Создание БД
echo ""
echo "7. Создание базы данных..."
echo "ВАЖНО: Если у вас новая установка MariaDB, пароль root может быть пустым."
echo "Если пароль пустой - просто нажмите Enter"
read -sp "Введите пароль root для MariaDB (или Enter если пусто): " MYSQL_ROOT_PASSWORD
echo ""

if [ -z "$MYSQL_ROOT_PASSWORD" ]; then
    mysql -u root < database/schema.sql
else
    mysql -u root -p"$MYSQL_ROOT_PASSWORD" < database/schema.sql
fi
echo "База данных создана!"

# Создание директорий
echo ""
echo "8. Создание директорий..."
mkdir -p uploads logs
chmod 755 uploads logs

# Создание systemd service для Flask приложения
echo ""
echo "9. Создание systemd service..."
cat > /etc/systemd/system/phone-proxy.service << EOF
[Unit]
Description=Phone Proxy System Flask Application
After=network.target mariadb.service

[Service]
Type=simple
User=root
Group=root
WorkingDirectory=$PROJECT_DIR
Environment="PATH=$PROJECT_DIR/venv/bin"
ExecStart=$PROJECT_DIR/venv/bin/gunicorn -w 4 -b 0.0.0.0:5000 run:app
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# Запуск сервиса
systemctl daemon-reload
systemctl start phone-proxy
systemctl enable phone-proxy

echo ""
echo "======================================"
echo "Установка завершена!"
echo "======================================"
echo ""
echo "Веб-интерфейс доступен по адресу: http://$(hostname -I | awk '{print $1}'):5000"
echo ""
echo "Проверка статуса:"
echo "  systemctl status phone-proxy"
echo ""
echo "Логи:"
echo "  journalctl -u phone-proxy -f"
echo ""
echo "ВНИМАНИЕ: Asterisk НЕ установлен!"
echo "Для установки Asterisk используйте: ./install.sh"
echo ""


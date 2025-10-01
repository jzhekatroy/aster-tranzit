#!/bin/bash

###############################################################################
# Phone Proxy System - Автоматическая установка
# Для Ubuntu/Debian серверов
###############################################################################

set -e  # Остановка при ошибке

echo "======================================"
echo "Phone Proxy System - Установка"
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
apt-get upgrade -y

# Установка Python и зависимостей
echo ""
echo "2. Установка Python и pip..."
apt-get install -y python3 python3-pip python3-venv python3-dev build-essential

# Установка MySQL/MariaDB
echo ""
echo "3. Установка MySQL/MariaDB..."
# Сначала пробуем MariaDB (стандарт для Debian/Ubuntu)
if apt-cache show mariadb-server &>/dev/null; then
    echo "Устанавливаем MariaDB (полностью совместим с MySQL)..."
    apt-get install -y mariadb-server mariadb-client
    DB_SERVICE="mariadb"
elif apt-get install -y mysql-server mysql-client 2>/dev/null; then
    echo "Устанавливаем MySQL..."
    DB_SERVICE="mysql"
else
    echo "ОШИБКА: Не удалось установить MySQL или MariaDB"
    exit 1
fi

# Запуск MySQL/MariaDB
systemctl start $DB_SERVICE
systemctl enable $DB_SERVICE
echo "База данных $DB_SERVICE установлена и запущена!"

# Установка Asterisk
echo ""
echo "4. Установка Asterisk..."

# Проверяем есть ли Asterisk в репозиториях
if apt-cache show asterisk &>/dev/null; then
    echo "Устанавливаем Asterisk из репозитория..."
    apt-get install -y asterisk asterisk-mysql
else
    echo "Asterisk не найден в репозиториях, компилируем из исходников..."
    echo "Это займет 10-15 минут..."
    
    # Установка зависимостей для компиляции
    apt-get install -y build-essential wget libssl-dev libncurses5-dev \
        libnewt-dev libxml2-dev linux-headers-$(uname -r) libsqlite3-dev \
        uuid-dev libjansson-dev libedit-dev subversion git curl
    
    # Скачивание Asterisk
    cd /usr/src
    ASTERISK_VERSION="20.10.0"
    
    if [ ! -d "asterisk-${ASTERISK_VERSION}" ]; then
        echo "Скачиваем Asterisk ${ASTERISK_VERSION}..."
        wget -q "https://downloads.asterisk.org/pub/telephony/asterisk/asterisk-${ASTERISK_VERSION}.tar.gz"
        tar -xzf "asterisk-${ASTERISK_VERSION}.tar.gz"
        rm "asterisk-${ASTERISK_VERSION}.tar.gz"
    fi
    
    cd "asterisk-${ASTERISK_VERSION}"
    
    # Установка дополнительных зависимостей
    echo "Устанавливаем зависимости Asterisk..."
    ./contrib/scripts/install_prereq install -y
    
    # Конфигурация и компиляция
    echo "Конфигурируем Asterisk..."
    ./configure --with-jansson-bundled --with-pjproject-bundled
    
    echo "Компилируем Asterisk (это займет время)..."
    make -j$(nproc)
    
    echo "Устанавливаем Asterisk..."
    make install
    make samples
    make config
    
    # Создание пользователя asterisk
    if ! id asterisk &>/dev/null; then
        groupadd asterisk
        useradd -r -d /var/lib/asterisk -g asterisk asterisk
    fi
    
    # Установка прав
    chown -R asterisk:asterisk /var/lib/asterisk /var/spool/asterisk /var/log/asterisk /var/run/asterisk /etc/asterisk
    
    # Настройка systemd
    if [ ! -f /etc/systemd/system/asterisk.service ]; then
        cat > /etc/systemd/system/asterisk.service << 'ASTERISKEOF'
[Unit]
Description=Asterisk PBX
After=network.target

[Service]
Type=forking
User=asterisk
Group=asterisk
ExecStart=/usr/sbin/asterisk -f -C /etc/asterisk/asterisk.conf
ExecReload=/usr/sbin/asterisk -rx 'core reload'
Restart=always

[Install]
WantedBy=multi-user.target
ASTERISKEOF
        systemctl daemon-reload
    fi
    
    cd "$PROJECT_DIR"
    echo "Asterisk установлен из исходников!"
fi

# Установка ODBC для Asterisk
echo ""
echo "5. Установка ODBC драйверов..."
apt-get install -y unixodbc unixodbc-dev odbc-mariadb

# Запуск Asterisk
systemctl start asterisk
systemctl enable asterisk

# Создание виртуального окружения Python
echo ""
echo "6. Создание виртуального окружения Python..."
cd "$PROJECT_DIR"
python3 -m venv venv
source venv/bin/activate

# Установка Python зависимостей
echo ""
echo "7. Установка Python зависимостей..."
pip install --upgrade pip
pip install -r requirements.txt

# Создание .env файла
echo ""
echo "8. Создание конфигурации..."
if [ ! -f .env ]; then
    cp .env.example .env
    echo "Создан файл .env. Пожалуйста, отредактируйте его при необходимости."
else
    echo "Файл .env уже существует."
fi

# Создание БД
echo ""
echo "9. Создание базы данных..."
echo "ВАЖНО: Если у вас новая установка MariaDB, пароль root может быть пустым."
echo "Если пароль пустой - просто нажмите Enter"
read -sp "Введите пароль root для MySQL/MariaDB (или Enter если пусто): " MYSQL_ROOT_PASSWORD
echo ""

if [ -z "$MYSQL_ROOT_PASSWORD" ]; then
    # Пустой пароль - подключаемся без пароля
    mysql -u root < database/schema.sql
else
    # С паролем
    mysql -u root -p"$MYSQL_ROOT_PASSWORD" < database/schema.sql
fi
echo "База данных создана!"

# Создание директории для uploads
echo ""
echo "10. Создание директорий..."
mkdir -p uploads
mkdir -p logs
chmod 755 uploads logs

# Настройка ODBC
echo ""
echo "11. Настройка ODBC..."
if [ ! -f /etc/odbc.ini ]; then
    cp asterisk/odbc.ini.example /etc/odbc.ini
    echo "ODBC настроен. Проверьте /etc/odbc.ini"
else
    echo "Файл /etc/odbc.ini уже существует. Добавьте конфигурацию вручную из asterisk/odbc.ini.example"
fi

# Копирование конфигов Asterisk
echo ""
echo "12. Настройка Asterisk..."
echo "ВНИМАНИЕ: Конфигурационные файлы Asterisk находятся в директории asterisk/"
echo "Вам нужно вручную скопировать или включить их в ваши конфиги Asterisk:"
echo "  - asterisk/extensions.conf -> /etc/asterisk/extensions.conf"
echo "  - asterisk/res_odbc.conf -> /etc/asterisk/res_odbc.conf"
echo "  - asterisk/func_odbc.conf -> /etc/asterisk/func_odbc.conf"
echo ""
read -p "Скопировать конфиги автоматически? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    # Бэкап существующих конфигов
    if [ -f /etc/asterisk/extensions.conf ]; then
        cp /etc/asterisk/extensions.conf /etc/asterisk/extensions.conf.backup
    fi
    
    # Копирование или добавление конфигов
    cat asterisk/extensions.conf >> /etc/asterisk/extensions.conf
    cp asterisk/res_odbc.conf /etc/asterisk/res_odbc.conf
    cp asterisk/func_odbc.conf /etc/asterisk/func_odbc.conf
    
    echo "Конфиги скопированы!"
fi

# Перезапуск Asterisk для применения конфигурации
echo ""
echo "13. Перезапуск Asterisk для применения конфигурации..."
systemctl restart asterisk

# Создание systemd service для Flask приложения
echo ""
echo "14. Создание systemd service..."
cat > /etc/systemd/system/phone-proxy.service << EOF
[Unit]
Description=Phone Proxy System Flask Application
After=network.target mysql.service mariadb.service

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=$PROJECT_DIR
Environment="PATH=$PROJECT_DIR/venv/bin"
ExecStart=$PROJECT_DIR/venv/bin/gunicorn -w 4 -b 0.0.0.0:5000 run:app
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# Установка прав
chown -R www-data:www-data "$PROJECT_DIR"

# Запуск сервиса
systemctl daemon-reload
systemctl start phone-proxy
systemctl enable phone-proxy

echo ""
echo "======================================"
echo "Установка завершена!"
echo "======================================"
echo ""
echo "Веб-интерфейс доступен по адресу: http://your-server-ip:5000"
echo ""
echo "Следующие шаги:"
echo "1. Отредактируйте .env файл с вашими настройками"
echo "2. Настройте SIP транки в /etc/asterisk/sip.conf (см. asterisk/sip.conf.example)"
echo "3. Проверьте подключение ODBC: isql phone_proxy_dsn"
echo "4. Перезапустите сервисы: systemctl restart phone-proxy asterisk"
echo ""
echo "Проверка статуса:"
echo "  systemctl status phone-proxy"
echo "  systemctl status asterisk"
echo ""
echo "Логи:"
echo "  journalctl -u phone-proxy -f"
echo "  tail -f /var/log/asterisk/full"
echo ""


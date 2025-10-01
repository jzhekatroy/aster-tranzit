# Инструкция по установке Phone Proxy System

## Автоматическая установка (рекомендуется)

```bash
# Клонируйте репозиторий
git clone https://github.com/jzhekatroy/aster-tranzit.git
cd aster-tranzit

# Запустите скрипт установки
chmod +x install.sh
sudo ./install.sh
```

Скрипт автоматически установит:
- Python 3 и зависимости
- MySQL Server
- Asterisk
- ODBC драйверы
- Создаст базу данных
- Настроит systemd сервисы

## Ручная установка

### 1. Установка зависимостей

```bash
# Обновление системы
sudo apt-get update
sudo apt-get upgrade -y

# Python
sudo apt-get install -y python3 python3-pip python3-venv python3-dev

# MySQL
sudo apt-get install -y mysql-server mysql-client

# Asterisk
sudo apt-get install -y asterisk asterisk-mysql

# ODBC
sudo apt-get install -y unixodbc unixodbc-dev odbc-mariadb
```

### 2. Настройка MySQL

```bash
# Запуск MySQL
sudo systemctl start mysql
sudo systemctl enable mysql

# Создание базы данных
sudo mysql -u root -p < database/schema.sql
```

### 3. Настройка Python приложения

```bash
# Создание виртуального окружения
python3 -m venv venv
source venv/bin/activate

# Установка зависимостей
pip install -r requirements.txt

# Создание .env файла
cp .env.example .env
nano .env  # Отредактируйте настройки
```

### 4. Настройка ODBC

```bash
# Копирование конфигурации
sudo cp asterisk/odbc.ini.example /etc/odbc.ini
sudo nano /etc/odbc.ini  # Проверьте настройки

# Проверка подключения
isql phone_proxy_dsn asterisk asterisk
```

### 5. Настройка Asterisk

```bash
# Копирование конфигураций
sudo cp asterisk/res_odbc.conf /etc/asterisk/
sudo cp asterisk/func_odbc.conf /etc/asterisk/

# Добавление dialplan в extensions.conf
sudo nano /etc/asterisk/extensions.conf
# Добавьте содержимое из asterisk/extensions.conf

# Настройка SIP транков
sudo nano /etc/asterisk/sip.conf
# Используйте asterisk/sip.conf.example как пример

# Перезапуск Asterisk
sudo systemctl restart asterisk
sudo systemctl enable asterisk
```

### 6. Запуск приложения

#### Для разработки:
```bash
python run.py
```

#### Для продакшена (с Gunicorn):
```bash
gunicorn -w 4 -b 0.0.0.0:5000 run:app
```

#### Или через systemd:
```bash
sudo cp phone-proxy.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl start phone-proxy
sudo systemctl enable phone-proxy
```

## Проверка установки

### 1. Проверка веб-приложения
```bash
curl http://localhost:5000/health
```

### 2. Проверка Asterisk
```bash
sudo asterisk -rx "core show version"
sudo asterisk -rx "odbc show all"
sudo asterisk -rx "module show like func_odbc"
```

### 3. Проверка подключения к БД
```bash
mysql -u asterisk -p phone_proxy -e "SELECT COUNT(*) FROM phone_mappings;"
```

## Настройка SIP транков

Отредактируйте `/etc/asterisk/sip.conf`:

```ini
[inbound-trunk]
type=peer
host=your-sip-provider.com
username=your_username
secret=your_password
context=incoming
insecure=port,invite

[outbound-trunk]
type=peer
host=your-outbound-provider.com
username=your_outbound_username
secret=your_outbound_password
context=outbound
```

## Использование

1. Откройте веб-интерфейс: `http://your-server:5000`
2. Загрузите CSV файл с реальными номерами
3. Система сгенерирует фейковые номера
4. Настройте входящие звонки на фейковые номера
5. Asterisk автоматически перенаправит их на реальные

## Логи

```bash
# Логи Flask приложения
sudo journalctl -u phone-proxy -f

# Логи Asterisk
sudo tail -f /var/log/asterisk/full
```

## Безопасность

1. **Измените пароли в .env**
2. **Настройте firewall**:
```bash
sudo ufw allow 5000/tcp  # Flask
sudo ufw allow 5060/tcp  # SIP
sudo ufw allow 10000:20000/udp  # RTP
```
3. **Используйте HTTPS** (настройте Nginx reverse proxy)
4. **Ограничьте доступ к веб-интерфейсу**

## Troubleshooting

### Проблема: Asterisk не может подключиться к БД
```bash
# Проверьте ODBC
isql phone_proxy_dsn asterisk asterisk

# Проверьте логи
sudo asterisk -rx "odbc show all"
```

### Проблема: Веб-приложение не запускается
```bash
# Проверьте логи
sudo journalctl -u phone-proxy -n 50

# Проверьте .env
cat .env

# Проверьте подключение к MySQL
mysql -u phone_proxy_app -p phone_proxy
```

### Проблема: Звонки не переадресуются
```bash
# Проверьте dialplan
sudo asterisk -rx "dialplan show incoming"

# Проверьте что функция ODBC работает
sudo asterisk -rx "odbc show"

# Проверьте логи звонков
sudo tail -f /var/log/asterisk/full | grep PHONE_LOOKUP
```

## Поддержка

Для вопросов и проблем создавайте issue на GitHub:
https://github.com/jzhekatroy/aster-tranzit/issues


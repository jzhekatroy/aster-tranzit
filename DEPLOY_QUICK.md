# Быстрое развертывание на сервере

## 1. Подключение к серверу
```bash
ssh root@your-server-ip
```

## 2. Клонирование проекта
```bash
cd /opt
git clone https://github.com/jzhekatroy/aster-tranzit.git
cd aster-tranzit
```

## 3. Автоматическая установка
```bash
chmod +x install.sh
./install.sh
```

Скрипт спросит пароль root для MySQL. После установки:
- Flask API будет доступен на порту 5000
- Asterisk будет настроен и запущен
- База данных создана

## 4. Настройка конфигурации

### Отредактируйте .env
```bash
nano .env
```

Измените пароли и настройки:
```
FLASK_SECRET_KEY=your-strong-secret-key
MYSQL_PASSWORD=your-mysql-password
```

### Настройте SIP транки
```bash
nano /etc/asterisk/sip.conf
```

Используйте `asterisk/sip.conf.example` как шаблон.

## 5. Перезапуск сервисов
```bash
systemctl restart phone-proxy
systemctl restart asterisk
```

## 6. Проверка работы

### Проверка веб-интерфейса
```bash
curl http://localhost:5000/health
```

### Проверка Asterisk
```bash
asterisk -rx "odbc show all"
asterisk -rx "dialplan show incoming"
```

### Проверка БД
```bash
mysql -u asterisk -p phone_proxy -e "SHOW TABLES;"
```

## 7. Открытие портов в firewall
```bash
ufw allow 5000/tcp   # Flask API
ufw allow 5060/tcp   # SIP signaling
ufw allow 5060/udp   # SIP signaling
ufw allow 10000:20000/udp  # RTP (голос)
```

## 8. Доступ к веб-интерфейсу
Откройте в браузере:
```
http://your-server-ip:5000
```

## Команды для управления

### Статус сервисов
```bash
systemctl status phone-proxy
systemctl status asterisk
systemctl status mysql
```

### Логи
```bash
# Flask API
journalctl -u phone-proxy -f

# Asterisk
tail -f /var/log/asterisk/full

# MySQL
tail -f /var/log/mysql/error.log
```

### Перезапуск
```bash
systemctl restart phone-proxy
systemctl restart asterisk
```

## Тестирование

### 1. Загрузите тестовый файл
Используйте `test_phones.csv` из проекта

### 2. Проверьте API
```bash
# Загрузка номеров
curl -F "file=@test_phones.csv" http://localhost:5000/upload

# Просмотр всех маппингов
curl http://localhost:5000/mappings

# Поиск реального номера
curl http://localhost:5000/lookup/real/700000000000001
```

### 3. Тест Asterisk
```bash
# Войдите в Asterisk CLI
asterisk -r

# Проверьте ODBC
odbc show all

# Проверьте функцию поиска
dialplan show incoming
```

## Production готовность

### Обязательно:
- ✅ Измените все пароли в .env и MySQL
- ✅ Настройте HTTPS через Nginx
- ✅ Настройте автоматические бэкапы
- ✅ Настройте мониторинг

### Рекомендуется:
- Настройте логротацию
- Добавьте SSL сертификаты для SIP (TLS)
- Настройте fail2ban
- Добавьте мониторинг (Prometheus, Grafana)

## Проблемы и решения

### Flask не запускается
```bash
# Проверьте права
chown -R www-data:www-data /opt/aster-tranzit

# Проверьте виртуальное окружение
cd /opt/aster-tranzit
source venv/bin/activate
pip list
```

### Asterisk не подключается к БД
```bash
# Проверьте ODBC
isql phone_proxy_dsn asterisk asterisk

# Если не работает, проверьте /etc/odbc.ini
cat /etc/odbc.ini
```

### MySQL ошибки доступа
```bash
# Дайте права пользователю
mysql -u root -p
GRANT ALL PRIVILEGES ON phone_proxy.* TO 'asterisk'@'localhost';
FLUSH PRIVILEGES;
```

## Контакты
При возникновении проблем создавайте issue:
https://github.com/jzhekatroy/aster-tranzit/issues


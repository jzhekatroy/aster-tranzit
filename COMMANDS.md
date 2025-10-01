# Команды для работы с проектом

## На сервере для установки

```bash
# 1. Клонировать репозиторий
git clone https://github.com/jzhekatroy/aster-tranzit.git
cd aster-tranzit

# 2. Запустить установку
chmod +x install.sh
sudo ./install.sh

# 3. Отредактировать конфигурацию
sudo nano .env

# 4. Перезапустить сервисы
sudo systemctl restart phone-proxy
sudo systemctl restart asterisk
```

## Проверка работы

```bash
# Статус сервисов
sudo systemctl status phone-proxy
sudo systemctl status asterisk
sudo systemctl status mysql

# Проверка API
curl http://localhost:5000/health

# Проверка Asterisk
sudo asterisk -rx "odbc show all"
sudo asterisk -rx "module show like func_odbc"
```

## Логи

```bash
# Логи Flask
sudo journalctl -u phone-proxy -f

# Логи Asterisk
sudo tail -f /var/log/asterisk/full

# Логи MySQL
sudo tail -f /var/log/mysql/error.log
```

## Обновление проекта

```bash
cd /opt/aster-tranzit
git pull
sudo systemctl restart phone-proxy
sudo systemctl restart asterisk
```

## Бэкап

```bash
# Бэкап базы данных
mysqldump -u root -p phone_proxy > backup_$(date +%Y%m%d).sql

# Бэкап конфигов Asterisk
tar -czf asterisk_config_$(date +%Y%m%d).tar.gz /etc/asterisk/
```


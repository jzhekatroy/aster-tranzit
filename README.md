# Phone Proxy System (Aster-Tranzit)

Система проксирования телефонных номеров с использованием Asterisk.

## Описание

Система позволяет:
1. Загружать список реальных телефонных номеров через веб-интерфейс
2. Генерировать для каждого номера уникальный 15-значный фейковый номер
3. Сохранять связки реальных и фейковых номеров в БД
4. Автоматически маршрутизировать входящие звонки с фейковых номеров на реальные через Asterisk

## Архитектура

- **Backend**: Python Flask API
- **Frontend**: HTML + JavaScript (загрузка CSV файлов)
- **Database**: MySQL
- **Telephony**: Asterisk с подключением к MySQL

## Быстрый старт

### Требования
- Ubuntu/Debian сервер
- Python 3.8+
- MySQL 8.0+ или MariaDB 10.5+
- Asterisk 18+

### Установка

```bash
# Клонировать репозиторий
git clone https://github.com/jzhekatroy/aster-tranzit.git
cd aster-tranzit

# Запустить скрипт автоматической установки
chmod +x install.sh
sudo ./install.sh
```

### Ручная установка

См. [INSTALL.md](INSTALL.md)

## Использование

1. Откройте веб-интерфейс: `http://your-server:5000`
2. Загрузите CSV файл с реальными номерами (один номер на строку)
3. Система сгенерирует и покажет фейковые номера
4. Настройте транки в Asterisk для входящих/исходящих звонков
5. Звонки на фейковые номера автоматически перенаправятся на реальные

## Структура проекта

```
.
├── app/                    # Flask приложение
│   ├── __init__.py
│   ├── routes.py          # API endpoints
│   ├── models.py          # Database models
│   └── utils.py           # Утилиты генерации номеров
├── static/                 # Статические файлы (CSS, JS)
├── templates/              # HTML шаблоны
├── asterisk/              # Конфигурация Asterisk
│   ├── extensions.conf    # Dialplan
│   └── res_odbc.conf      # Подключение к MySQL
├── database/              # SQL схемы
│   └── schema.sql
├── config.py              # Конфигурация приложения
├── requirements.txt       # Python зависимости
└── install.sh            # Скрипт установки
```

## Конфигурация

Создайте файл `.env`:

```
MYSQL_HOST=localhost
MYSQL_USER=asterisk
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=phone_proxy
FLASK_SECRET_KEY=your_secret_key
```

## Лицензия

MIT


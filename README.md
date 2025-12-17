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

Фоновый импорт CSV (актуальный режим):
1. Заполните `.env` (MySQL и пути каталогов, порт по умолчанию 3000).
2. Поместите файл `GGS_all_phones.csv` в каталог `data/incoming/` (разделитель `;`, первая строка — заголовок, колонка 1 `real_phone`, колонка 2 `fake_phone`).
3. Запустите воркер: `python import_worker.py` — он раз в минуту заберёт файл, очистит БД и загрузит новые данные. Результат в `GGS_all_phones.csv.OK` или `.fail`, исходник уедет в `data/archive/` с таймстампом.
4. Health/status доступен на `http://localhost:3000/health` и `/status`.

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


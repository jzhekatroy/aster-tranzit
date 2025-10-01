# Архитектура Phone Proxy System

## Общая схема

```
┌──────────────┐
│ Пользователь │
└──────┬───────┘
       │ Загружает CSV
       ▼
┌──────────────────┐
│ Веб-интерфейс    │
│ (HTML + JS)      │
└──────┬───────────┘
       │ HTTP POST
       ▼
┌──────────────────┐
│ Flask API        │
│ - Парсинг CSV    │
│ - Генерация      │
│ - Валидация      │
└──────┬───────────┘
       │ SQL
       ▼
┌──────────────────┐
│ MySQL Database   │
│ - phone_mappings │
│ - call_logs      │
└──────┬───────────┘
       │ ODBC / HTTP
       ▼
┌──────────────────┐      ┌─────────────┐
│ Asterisk         │◄────►│ SIP Trunk   │
│ - Dialplan       │      │ (IN/OUT)    │
│ - ODBC lookup    │      └─────────────┘
└──────────────────┘
```

## Компоненты

### 1. Веб-интерфейс
- **Технологии**: HTML5, CSS3, Vanilla JavaScript
- **Функции**:
  - Загрузка CSV файлов
  - Отображение результатов генерации
  - Просмотр всех маппингов
  - Экспорт в CSV

### 2. Flask API Server
- **Технологии**: Python 3.8+, Flask, mysql-connector
- **Endpoints**:
  - `POST /upload` - Загрузка CSV и генерация фейковых номеров
  - `GET /mappings` - Получение всех маппингов
  - `GET /lookup/real/<fake_phone>` - Получение реального номера (для Asterisk)
  - `GET /lookup/fake/<real_phone>` - Получение фейкового номера
  - `GET /export/csv` - Экспорт всех маппингов
  - `GET /health` - Health check

### 3. База данных MySQL
- **Таблицы**:
  - `phone_mappings` - Связки реальных и фейковых номеров
  - `call_logs` - Логи звонков
  
#### Схема phone_mappings
```sql
id INT PRIMARY KEY AUTO_INCREMENT
real_phone VARCHAR(20) UNIQUE
fake_phone VARCHAR(20) UNIQUE
created_at TIMESTAMP
updated_at TIMESTAMP
```

#### Схема call_logs
```sql
id INT PRIMARY KEY AUTO_INCREMENT
fake_phone VARCHAR(20)
real_phone VARCHAR(20)
caller_id VARCHAR(50)
call_timestamp TIMESTAMP
call_duration INT
call_status VARCHAR(20)
```

### 4. Asterisk PBX
- **Конфигурация**:
  - `extensions.conf` - Dialplan для маршрутизации
  - `res_odbc.conf` - Подключение к MySQL
  - `func_odbc.conf` - SQL функции
  - `sip.conf` - SIP транки

#### Логика маршрутизации
1. Входящий звонок на фейковый номер → контекст `[incoming]`
2. Asterisk делает запрос к БД через ODBC
3. Получает реальный номер
4. Делает исходящий звонок через outbound транк
5. Логирует звонок

## Потоки данных

### Поток 1: Загрузка номеров
```
CSV файл → Flask → Парсинг → Валидация → 
→ Генерация фейковых → Проверка уникальности → 
→ Сохранение в БД → Возврат пользователю
```

### Поток 2: Входящий звонок
```
SIP Trunk IN → Asterisk → Dialplan [incoming] → 
→ ODBC запрос к БД → Получение реального номера → 
→ Dial() на outbound транк → Логирование
```

### Поток 3: API запрос (альтернатива ODBC)
```
Asterisk → HTTP GET /lookup/real/{fake} → 
→ Flask API → MySQL запрос → 
→ JSON ответ → Asterisk продолжает dialplan
```

## Масштабируемость

### Горизонтальное масштабирование
- **Flask API**: Можно запускать несколько инстансов за load balancer
- **MySQL**: Master-Slave репликация для чтения
- **Asterisk**: Несколько серверов с общей БД

### Производительность
- **Индексы БД**: На fake_phone и real_phone для быстрого поиска
- **Connection pooling**: Asterisk ODBC поддерживает пул соединений
- **Кэширование**: Можно добавить Redis для горячих номеров

## Безопасность

### Уровень приложения
- Валидация входных данных
- Защита от SQL injection (использование параметризованных запросов)
- Rate limiting (можно добавить)

### Уровень сети
- Firewall правила (UFW)
- Ограничение доступа к API по IP
- VPN для Asterisk SIP трафика

### Уровень БД
- Отдельные пользователи с минимальными правами
- Asterisk: только SELECT на phone_mappings
- Flask: полные права на свои таблицы

## Мониторинг

### Метрики для отслеживания
- Количество активных маппингов
- Количество звонков в день
- Процент успешных переадресаций
- Время ответа API
- Использование ресурсов (CPU, RAM, DB connections)

### Логирование
- Flask: Gunicorn access logs + application logs
- Asterisk: /var/log/asterisk/full
- MySQL: slow query log

## Резервное копирование

### База данных
```bash
# Ежедневный бэкап
mysqldump phone_proxy > backup_$(date +%Y%m%d).sql
```

### Конфигурация Asterisk
```bash
# Бэкап конфигов
tar -czf asterisk_config_$(date +%Y%m%d).tar.gz /etc/asterisk/
```

## Восстановление после сбоя

### Сценарий 1: Падение Flask API
- systemd автоматически перезапустит сервис
- Asterisk может использовать ODBC напрямую (не зависит от Flask)

### Сценарий 2: Падение MySQL
- Asterisk попытается переподключиться (настройка в res_odbc.conf)
- Flask вернет ошибки 503, пользователи увидят сообщение

### Сценарий 3: Падение Asterisk
- Звонки не будут обрабатываться
- systemd перезапустит Asterisk
- Веб-интерфейс продолжит работать

## Развертывание

### Production чеклист
- [ ] Изменить все пароли в .env
- [ ] Настроить HTTPS (Nginx reverse proxy)
- [ ] Настроить firewall
- [ ] Настроить мониторинг
- [ ] Настроить бэкапы
- [ ] Протестировать failover сценарии
- [ ] Документировать все изменения конфигурации

## Дальнейшее развитие

### Возможные улучшения
1. **Web UI**: Добавить аутентификацию пользователей
2. **API**: Добавить REST API для интеграций
3. **Analytics**: Dashboard с аналитикой звонков
4. **Notifications**: Уведомления о звонках (Telegram, Email)
5. **Multi-tenancy**: Поддержка нескольких клиентов
6. **WebRTC**: Веб-интерфейс для звонков


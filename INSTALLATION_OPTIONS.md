# Варианты установки Phone Proxy System

## Вариант 1: Упрощенная установка (РЕКОМЕНДУЕТСЯ для начала)

**Только веб-интерфейс + API + база данных**  
Без Asterisk (можно добавить потом)

```bash
git clone https://github.com/jzhekatroy/aster-tranzit.git
cd aster-tranzit
chmod +x install-simple.sh
sudo ./install-simple.sh
```

**Время установки:** ~3-5 минут  
**Что установится:**
- ✅ MariaDB
- ✅ Python Flask приложение
- ✅ Веб-интерфейс на порту 5000
- ❌ Asterisk (не устанавливается)

**Когда использовать:**
- Хочешь просто попробовать веб-интерфейс
- Нужно только генерировать фейковые номера
- Asterisk установишь позже вручную

---

## Вариант 2: Полная установка

**Всё включено: веб + API + база данных + Asterisk**

```bash
git clone https://github.com/jzhekatroy/aster-tranzit.git
cd aster-tranzit
chmod +x install.sh
sudo ./install.sh
```

**Время установки:** ~15-20 минут (компиляция Asterisk)  
**Что установится:**
- ✅ MariaDB
- ✅ Python Flask приложение
- ✅ Веб-интерфейс на порту 5000
- ✅ Asterisk (компилируется из исходников)
- ✅ ODBC драйверы
- ✅ Все конфигурации

**Когда использовать:**
- Нужна полная рабочая система сразу
- Готов подождать 15-20 минут компиляции
- Сразу будешь настраивать SIP транки

---

## Вариант 3: Ручная установка

Если скрипты не работают или нужен полный контроль.

См. подробную инструкцию: [INSTALL.md](INSTALL.md)

---

## Что выбрать?

### 🟢 Начни с **Варианта 1** (install-simple.sh)
- Быстро установится
- Проверишь что всё работает
- Потом добавишь Asterisk если нужно

### 🟡 Используй **Вариант 2** (install.sh)
- Если сразу нужна полная система
- Если есть время подождать компиляцию
- Если уже есть настроенные SIP транки

### 🔴 Используй **Вариант 3** (вручную)
- Если скрипты не работают на твоей системе
- Если нужна кастомная конфигурация
- Если разбираешься в Linux

---

## После установки

### Проверка веб-интерфейса
```bash
# Открой в браузере
http://your-server-ip:5000

# Или проверь через curl
curl http://localhost:5000/health
```

### Проверка сервисов
```bash
systemctl status phone-proxy
systemctl status mariadb
systemctl status asterisk  # Если установлен
```

### Логи
```bash
journalctl -u phone-proxy -f
```

---

## Добавление Asterisk после упрощенной установки

Если установил через `install-simple.sh` и теперь нужен Asterisk:

```bash
# Установи зависимости
apt-get install -y build-essential wget libssl-dev libncurses5-dev \
    libnewt-dev libxml2-dev linux-headers-$(uname -r) libsqlite3-dev \
    uuid-dev libjansson-dev libedit-dev

# Скачай и скомпилируй Asterisk
cd /usr/src
wget https://downloads.asterisk.org/pub/telephony/asterisk/asterisk-20.10.0.tar.gz
tar -xzf asterisk-20.10.0.tar.gz
cd asterisk-20.10.0
./contrib/scripts/install_prereq install -y
./configure --with-jansson-bundled --with-pjproject-bundled
make -j$(nproc)
make install
make samples
make config

# Настрой конфигурацию
cd /path/to/aster-tranzit
cp asterisk/res_odbc.conf /etc/asterisk/
cp asterisk/func_odbc.conf /etc/asterisk/
cat asterisk/extensions.conf >> /etc/asterisk/extensions.conf

# Установи ODBC
apt-get install -y unixodbc unixodbc-dev odbc-mariadb
cp asterisk/odbc.ini.example /etc/odbc.ini

# Запусти Asterisk
systemctl start asterisk
systemctl enable asterisk
```

---

## Проблемы?

См. [INSTALL.md](INSTALL.md) раздел Troubleshooting


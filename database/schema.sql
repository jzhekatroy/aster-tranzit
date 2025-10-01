-- Phone Proxy System Database Schema
-- MySQL 8.0+

-- Создание базы данных
CREATE DATABASE IF NOT EXISTS phone_proxy CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE phone_proxy;

-- Таблица связок реальных и фейковых номеров
CREATE TABLE IF NOT EXISTS phone_mappings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    real_phone VARCHAR(20) NOT NULL UNIQUE COMMENT 'Реальный телефонный номер',
    fake_phone VARCHAR(20) NOT NULL UNIQUE COMMENT 'Фейковый телефонный номер',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT 'Дата создания связки',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT 'Дата обновления',
    
    INDEX idx_fake_phone (fake_phone),
    INDEX idx_real_phone (real_phone),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Связки реальных и фейковых номеров';

-- Таблица логов звонков
CREATE TABLE IF NOT EXISTS call_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    fake_phone VARCHAR(20) NOT NULL COMMENT 'Фейковый номер на который поступил звонок',
    real_phone VARCHAR(20) NOT NULL COMMENT 'Реальный номер на который переадресован звонок',
    caller_id VARCHAR(50) DEFAULT NULL COMMENT 'ID звонящего (опционально)',
    call_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT 'Время звонка',
    call_duration INT DEFAULT 0 COMMENT 'Длительность звонка в секундах',
    call_status VARCHAR(20) DEFAULT NULL COMMENT 'Статус звонка (ANSWERED, BUSY, NOANSWER, etc)',
    
    INDEX idx_fake_phone (fake_phone),
    INDEX idx_real_phone (real_phone),
    INDEX idx_call_timestamp (call_timestamp),
    
    FOREIGN KEY (fake_phone) REFERENCES phone_mappings(fake_phone) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Логи звонков';

-- Создание пользователя для Asterisk (опционально)
-- ВАЖНО: Измените пароль в продакшене!
CREATE USER IF NOT EXISTS 'asterisk'@'localhost' IDENTIFIED BY 'asterisk';
GRANT SELECT ON phone_proxy.phone_mappings TO 'asterisk'@'localhost';
GRANT INSERT ON phone_proxy.call_logs TO 'asterisk'@'localhost';

-- Создание пользователя для приложения (опционально)
CREATE USER IF NOT EXISTS 'phone_proxy_app'@'localhost' IDENTIFIED BY 'phone_proxy_pass';
GRANT ALL PRIVILEGES ON phone_proxy.* TO 'phone_proxy_app'@'localhost';

FLUSH PRIVILEGES;

-- Тестовые данные (опционально, для разработки)
-- INSERT INTO phone_mappings (real_phone, fake_phone) VALUES 
-- ('79001234567', '700000000000001'),
-- ('79009876543', '700000000000002'),
-- ('79005555555', '700000000000003');


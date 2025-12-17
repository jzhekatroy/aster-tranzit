import mysql.connector
from mysql.connector import Error
from config import Config
from datetime import datetime

class Database:
    """Класс для работы с MySQL базой данных"""
    
    def __init__(self):
        self.config = {
            'host': Config.MYSQL_HOST,
            'port': Config.MYSQL_PORT,
            'user': Config.MYSQL_USER,
            'password': Config.MYSQL_PASSWORD,
            'database': Config.MYSQL_DATABASE
        }
    
    def get_connection(self):
        """Получить подключение к БД"""
        try:
            connection = mysql.connector.connect(**self.config)
            return connection
        except Error as e:
            print(f"Ошибка подключения к MySQL: {e}")
            return None
    
    def create_tables(self):
        """Создать таблицы если их нет"""
        connection = self.get_connection()
        if not connection:
            return False
        
        try:
            cursor = connection.cursor()
            
            # Таблица связок номеров
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS phone_mappings (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    real_phone VARCHAR(20) NOT NULL UNIQUE,
                    fake_phone VARCHAR(20) NOT NULL UNIQUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_fake_phone (fake_phone),
                    INDEX idx_real_phone (real_phone)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)
            
            # Таблица логов звонков (опционально)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS call_logs (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    fake_phone VARCHAR(20) NOT NULL,
                    real_phone VARCHAR(20) NOT NULL,
                    call_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_fake_phone (fake_phone)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)
            
            connection.commit()
            cursor.close()
            return True
            
        except Error as e:
            print(f"Ошибка создания таблиц: {e}")
            return False
        finally:
            if connection.is_connected():
                connection.close()
    
    def insert_mapping(self, real_phone, fake_phone):
        """Добавить связку номеров"""
        connection = self.get_connection()
        if not connection:
            return False
        
        try:
            cursor = connection.cursor()
            cursor.execute(
                "INSERT INTO phone_mappings (real_phone, fake_phone) VALUES (%s, %s)",
                (real_phone, fake_phone)
            )
            connection.commit()
            cursor.close()
            return True
        except Error as e:
            print(f"Ошибка вставки маппинга: {e}")
            return False
        finally:
            if connection.is_connected():
                connection.close()
    
    def insert_mappings_batch(self, mappings):
        """Добавить множество связок за раз"""
        connection = self.get_connection()
        if not connection:
            return False
        
        try:
            cursor = connection.cursor()
            cursor.executemany(
                "INSERT INTO phone_mappings (real_phone, fake_phone) VALUES (%s, %s)",
                mappings
            )
            connection.commit()
            cursor.close()
            return True
        except Error as e:
            print(f"Ошибка batch вставки: {e}")
            return False
        finally:
            if connection.is_connected():
                connection.close()
    
    def get_real_phone(self, fake_phone):
        """Получить реальный номер по фейковому"""
        connection = self.get_connection()
        if not connection:
            return None
        
        try:
            cursor = connection.cursor()
            cursor.execute(
                "SELECT real_phone FROM phone_mappings WHERE fake_phone = %s",
                (fake_phone,)
            )
            result = cursor.fetchone()
            cursor.close()
            return result[0] if result else None
        except Error as e:
            print(f"Ошибка получения реального номера: {e}")
            return None
        finally:
            if connection.is_connected():
                connection.close()
    
    def get_fake_phone(self, real_phone):
        """Получить фейковый номер по реальному"""
        connection = self.get_connection()
        if not connection:
            return None
        
        try:
            cursor = connection.cursor()
            cursor.execute(
                "SELECT fake_phone FROM phone_mappings WHERE real_phone = %s",
                (real_phone,)
            )
            result = cursor.fetchone()
            cursor.close()
            return result[0] if result else None
        except Error as e:
            print(f"Ошибка получения фейкового номера: {e}")
            return None
        finally:
            if connection.is_connected():
                connection.close()
    
    def get_all_mappings(self):
        """Получить все связки"""
        connection = self.get_connection()
        if not connection:
            return []
        
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT * FROM phone_mappings ORDER BY created_at DESC")
            results = cursor.fetchall()
            cursor.close()
            return results
        except Error as e:
            print(f"Ошибка получения маппингов: {e}")
            return []
        finally:
            if connection.is_connected():
                connection.close()
    
    def log_call(self, fake_phone, real_phone):
        """Залогировать звонок"""
        connection = self.get_connection()
        if not connection:
            return False
        
        try:
            cursor = connection.cursor()
            cursor.execute(
                "INSERT INTO call_logs (fake_phone, real_phone) VALUES (%s, %s)",
                (fake_phone, real_phone)
            )
            connection.commit()
            cursor.close()
            return True
        except Error as e:
            print(f"Ошибка логирования звонка: {e}")
            return False
        finally:
            if connection.is_connected():
                connection.close()
    
    def clear_all_mappings(self):
        """Очистить все связки номеров"""
        connection = self.get_connection()
        if not connection:
            return False
        
        try:
            cursor = connection.cursor()
            cursor.execute("DELETE FROM phone_mappings")
            connection.commit()
            cursor.close()
            return True
        except Error as e:
            print(f"Ошибка очистки маппингов: {e}")
            return False
        finally:
            if connection.is_connected():
                connection.close()

    def replace_all_mappings(self, mappings):
        """
        Полностью заменить все маппинги на новые данные из файла.

        Args:
            mappings: список кортежей (real_phone, fake_phone)

        Returns:
            tuple(bool, str|None, int): успех, ошибка (если есть), количество вставок
        """
        connection = self.get_connection()
        if not connection:
            return False, "Нет подключения к БД", 0

        try:
            connection.start_transaction()
            cursor = connection.cursor()
            cursor.execute("DELETE FROM phone_mappings")
            if mappings:
                cursor.executemany(
                    "INSERT INTO phone_mappings (real_phone, fake_phone) VALUES (%s, %s)",
                    mappings
                )
            connection.commit()
            inserted = len(mappings)
            cursor.close()
            return True, None, inserted
        except Error as e:
            if connection.is_connected():
                connection.rollback()
            return False, str(e), 0
        finally:
            if connection.is_connected():
                connection.close()


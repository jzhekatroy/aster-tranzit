import random
import string
from config import Config

def generate_fake_phone(existing_phones=None):
    """
    Генерировать уникальный фейковый телефонный номер
    
    Args:
        existing_phones: Список уже существующих номеров для проверки уникальности
    
    Returns:
        str: 15-значный номер
    """
    if existing_phones is None:
        existing_phones = set()
    
    length = Config.FAKE_NUMBER_LENGTH
    prefix = Config.FAKE_NUMBER_PREFIX
    
    # Длина оставшейся части номера
    remaining_length = length - len(prefix)
    
    max_attempts = 1000
    for _ in range(max_attempts):
        # Генерируем случайные цифры
        random_part = ''.join(random.choices(string.digits, k=remaining_length))
        fake_phone = prefix + random_part
        
        if fake_phone not in existing_phones:
            return fake_phone
    
    raise ValueError(f"Не удалось сгенерировать уникальный номер после {max_attempts} попыток")


def normalize_phone(phone):
    """
    Нормализовать телефонный номер (убрать все кроме цифр)
    
    Args:
        phone: Строка с номером телефона
    
    Returns:
        str: Номер содержащий только цифры
    """
    return ''.join(filter(str.isdigit, str(phone)))


def validate_phone(phone):
    """
    Валидация телефонного номера
    
    Args:
        phone: Строка с номером
    
    Returns:
        bool: True если номер валидный
    """
    normalized = normalize_phone(phone)
    
    # Проверяем что есть хотя бы 10 цифр
    if len(normalized) < 10:
        return False
    
    # Проверяем что не слишком длинный
    if len(normalized) > 15:
        return False
    
    return True


def parse_csv_phones(file_path):
    """
    Парсить CSV файл с номерами телефонов
    
    Args:
        file_path: Путь к CSV файлу
    
    Returns:
        list: Список валидных номеров
    """
    phones = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                # Убираем пробелы и переносы строк
                phone = line.strip()
                
                if not phone:
                    continue
                
                # Нормализуем номер
                normalized = normalize_phone(phone)
                
                # Валидируем
                if validate_phone(normalized):
                    phones.append(normalized)
    
    except Exception as e:
        print(f"Ошибка чтения CSV: {e}")
        return []
    
    # Убираем дубликаты
    phones = list(set(phones))
    
    return phones


def allowed_file(filename):
    """
    Проверить что файл имеет разрешенное расширение
    
    Args:
        filename: Имя файла
    
    Returns:
        bool: True если расширение разрешено
    """
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS


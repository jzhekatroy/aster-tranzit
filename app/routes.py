from flask import Blueprint, render_template, request, jsonify, send_file, session, redirect, url_for
from functools import wraps
from werkzeug.utils import secure_filename
import os
from app.models import Database
from app.utils import (
    generate_fake_phone, 
    parse_csv_phones, 
    allowed_file,
    normalize_phone
)
from config import Config
import io

bp = Blueprint('main', __name__)
db = Database()

# Инициализация БД при старте
db.create_tables()

# Простая авторизация
USERNAME = 'admin'
PASSWORD = 'finenumbers2025'

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('main.login'))
        return f(*args, **kwargs)
    return decorated_function


@bp.route('/login', methods=['GET', 'POST'])
def login():
    """Страница авторизации"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username == USERNAME and password == PASSWORD:
            session['logged_in'] = True
            return redirect(url_for('main.index'))
        else:
            return render_template('login.html', error='Неверное имя пользователя или пароль')
    
    return render_template('login.html')


@bp.route('/logout')
def logout():
    """Выход из системы"""
    session.pop('logged_in', None)
    return redirect(url_for('main.login'))


@bp.route('/')
@login_required
def index():
    """Главная страница с формой загрузки"""
    return render_template('index.html')


@bp.route('/upload', methods=['POST'])
@login_required
def upload_file():
    """
    Загрузить CSV файл с номерами и сгенерировать фейковые
    
    Returns:
        JSON с фейковыми номерами или ошибкой
    """
    # Проверка наличия файла
    if 'file' not in request.files:
        return jsonify({'error': 'Файл не найден'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': 'Файл не выбран'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': 'Разрешены только CSV файлы'}), 400
    
    try:
        # Проверяем флаг очистки базы
        clear_old = request.form.get('clear_old', 'false').lower() == 'true'
        
        # Сохраняем файл
        filename = secure_filename(file.filename)
        filepath = os.path.join(Config.UPLOAD_FOLDER, filename)
        file.save(filepath)
        
        # Парсим номера из CSV
        real_phones = parse_csv_phones(filepath)
        
        if not real_phones:
            os.remove(filepath)
            return jsonify({'error': 'В файле не найдено валидных номеров'}), 400
        
        # Если нужно, очищаем базу
        if clear_old:
            db.clear_all_mappings()
            existing_fake_phones = set()
            existing_real_phones = set()
        else:
            # Получаем существующие фейковые номера для проверки уникальности
            existing_mappings = db.get_all_mappings()
            existing_fake_phones = {m['fake_phone'] for m in existing_mappings}
            existing_real_phones = {m['real_phone'] for m in existing_mappings}
        
        # Генерируем фейковые номера
        mappings = []
        results = []
        
        for real_phone in real_phones:
            # Проверяем что реальный номер еще не добавлен
            if real_phone in existing_real_phones:
                # Получаем существующий фейковый номер
                fake_phone = db.get_fake_phone(real_phone)
                results.append({
                    'real_phone': real_phone,
                    'fake_phone': fake_phone,
                    'status': 'existing'
                })
                continue
            
            # Генерируем новый фейковый номер
            fake_phone = generate_fake_phone(existing_fake_phones)
            existing_fake_phones.add(fake_phone)
            
            mappings.append((real_phone, fake_phone))
            results.append({
                'real_phone': real_phone,
                'fake_phone': fake_phone,
                'status': 'new'
            })
        
        # Сохраняем новые маппинги в БД
        if mappings:
            success = db.insert_mappings_batch(mappings)
            if not success:
                os.remove(filepath)
                return jsonify({'error': 'Ошибка сохранения в базу данных'}), 500
        
        # Удаляем загруженный файл
        os.remove(filepath)
        
        return jsonify({
            'success': True,
            'total': len(results),
            'new': len(mappings),
            'existing': len(results) - len(mappings),
            'mappings': results
        })
    
    except Exception as e:
        if os.path.exists(filepath):
            os.remove(filepath)
        return jsonify({'error': f'Ошибка обработки файла: {str(e)}'}), 500


@bp.route('/mappings', methods=['GET'])
@login_required
def get_mappings():
    """
    Получить все существующие связки
    
    Returns:
        JSON со списком всех маппингов
    """
    try:
        mappings = db.get_all_mappings()
        return jsonify({
            'success': True,
            'count': len(mappings),
            'mappings': mappings
        })
    except Exception as e:
        return jsonify({'error': f'Ошибка получения данных: {str(e)}'}), 500


@bp.route('/lookup/real/<fake_phone>', methods=['GET'])
def lookup_real(fake_phone):
    """
    API для Asterisk: получить реальный номер по фейковому
    
    Args:
        fake_phone: Фейковый номер
    
    Returns:
        JSON с реальным номером
    """
    try:
        normalized = normalize_phone(fake_phone)
        real_phone = db.get_real_phone(normalized)
        
        if real_phone:
            # Логируем звонок
            db.log_call(normalized, real_phone)
            
            return jsonify({
                'success': True,
                'real_phone': real_phone
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Номер не найден'
            }), 404
    
    except Exception as e:
        return jsonify({'error': f'Ошибка: {str(e)}'}), 500


@bp.route('/lookup/fake/<real_phone>', methods=['GET'])
def lookup_fake(real_phone):
    """
    Получить фейковый номер по реальному
    
    Args:
        real_phone: Реальный номер
    
    Returns:
        JSON с фейковым номером
    """
    try:
        normalized = normalize_phone(real_phone)
        fake_phone = db.get_fake_phone(normalized)
        
        if fake_phone:
            return jsonify({
                'success': True,
                'fake_phone': fake_phone
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Номер не найден'
            }), 404
    
    except Exception as e:
        return jsonify({'error': f'Ошибка: {str(e)}'}), 500


@bp.route('/export/csv', methods=['GET'])
def export_csv():
    """
    Экспортировать все маппинги в CSV
    
    Returns:
        CSV файл для скачивания
    """
    try:
        mappings = db.get_all_mappings()
        
        # Создаем CSV в памяти
        output = io.StringIO()
        output.write('Real Phone,Fake Phone,Created At\n')
        
        for mapping in mappings:
            output.write(f"{mapping['real_phone']},{mapping['fake_phone']},{mapping['created_at']}\n")
        
        # Создаем response
        output.seek(0)
        return send_file(
            io.BytesIO(output.getvalue().encode('utf-8')),
            mimetype='text/csv',
            as_attachment=True,
            download_name='phone_mappings.csv'
        )
    
    except Exception as e:
        return jsonify({'error': f'Ошибка экспорта: {str(e)}'}), 500


@bp.route('/clear', methods=['POST'])
@login_required
def clear_all():
    """
    Очистить все номера из базы данных
    
    Returns:
        JSON с результатом операции
    """
    try:
        success = db.clear_all_mappings()
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Все номера успешно удалены'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Ошибка при очистке базы данных'
            }), 500
    
    except Exception as e:
        return jsonify({'error': f'Ошибка: {str(e)}'}), 500


@bp.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    try:
        # Проверяем подключение к БД
        connection = db.get_connection()
        if connection:
            connection.close()
            return jsonify({'status': 'healthy', 'database': 'connected'})
        else:
            return jsonify({'status': 'unhealthy', 'database': 'disconnected'}), 503
    except Exception as e:
        return jsonify({'status': 'unhealthy', 'error': str(e)}), 503


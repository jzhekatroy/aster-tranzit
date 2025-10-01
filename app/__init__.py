from flask import Flask
from flask_cors import CORS
import os

def create_app():
    """Фабрика приложения Flask"""
    app = Flask(__name__, 
                template_folder='../templates',
                static_folder='../static')
    
    # Загрузка конфигурации
    app.config.from_object('config.Config')
    
    # CORS
    CORS(app)
    
    # Создание папки для загрузок
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Регистрация routes
    from app import routes
    app.register_blueprint(routes.bp)
    
    return app


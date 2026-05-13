import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from models import User, Group
from werkzeug.security import generate_password_hash

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['WTF_CSRF_ENABLED'] = False
    app.config['LOGIN_DISABLED'] = True  # ОТКЛЮЧАЕМ АВТОРИЗАЦИЮ ДЛЯ ТЕСТОВ
    
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            
            # Создаём тестового администратора
            admin = User(
                email='admin@test.com',
                password_hash=generate_password_hash('admin123'),
                name='Test Admin',
                role='admin'
            )
            db.session.add(admin)
            
            # Создаём тестовую группу
            group = Group(name='Test Group')
            db.session.add(group)
            
            # Создаём тестового преподавателя
            teacher = User(
                email='teacher@test.com',
                password_hash=generate_password_hash('teacher123'),
                name='Test Teacher',
                role='teacher'
            )
            db.session.add(teacher)
            
            db.session.commit()
            
            # Принудительный логин через сессию
            with client.session_transaction() as sess:
                sess['_user_id'] = str(admin.id)
                sess['_fresh'] = True
            
            yield client
            
            db.drop_all()
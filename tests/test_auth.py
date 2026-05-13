import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import User
from werkzeug.security import generate_password_hash, check_password_hash

def test_password_hashing():
    """Проверка хеширования пароля"""
    password = 'admin123'
    hash1 = generate_password_hash(password)
    hash2 = generate_password_hash(password)
    # Хеши должны быть разными (из-за соли)
    assert hash1 != hash2
    assert check_password_hash(hash1, password) is True
    assert check_password_hash(hash1, 'wrong') is False

def test_user_verify_password():
    """Проверка метода verify_password"""
    user = User(email='test@test.com', name='Test', role='admin')
    user.password = 'mypass'
    assert user.verify_password('mypass') is True
    assert user.verify_password('wrong') is False

def test_user_from_db_row():
    """Проверка создания пользователя из строки БД"""
    row = {
        'id': 10,
        'email': 'db@test.com',
        'password_hash': generate_password_hash('pass123'),
        'name': 'DB User',
        'role': 'student',
        'group_id': 5
    }
    user = User.from_db_row(row)
    assert user.id == 10
    assert user.email == 'db@test.com'
    assert user.name == 'DB User'
    assert user.role == 'student'
    assert user.group_id == 5
    assert user.verify_password('pass123') is True
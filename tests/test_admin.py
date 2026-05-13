import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import User, Group

def test_user_roles():
    """Проверка ролей пользователей"""
    admin = User(email='admin@test.com', name='Admin', role='admin')
    teacher = User(email='teacher@test.com', name='Teacher', role='teacher')
    student = User(email='student@test.com', name='Student', role='student')
    
    assert admin.role == 'admin'
    assert teacher.role == 'teacher'
    assert student.role == 'student'

def test_group_creation():
    """Проверка создания группы"""
    group = Group(name='Test Group')
    assert group.name == 'Test Group'
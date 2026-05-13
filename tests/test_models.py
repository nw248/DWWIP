import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import User, Group, Course, Lesson, Question, Assignment, TestAnswer
from werkzeug.security import generate_password_hash, check_password_hash

def test_create_user():
    user = User(
        email='test@example.com',
        password_hash='hash',
        name='Test User',
        role='student'
    )
    assert user.email == 'test@example.com'
    assert user.name == 'Test User'
    assert user.role == 'student'

def test_user_password_hash():
    user = User(email='test@example.com', name='Test', role='student')
    user.password = 'mypassword'
    assert user.password_hash is not None
    assert user.password_hash != 'mypassword'
    assert user.verify_password('mypassword') is True

def test_create_group():
    group = Group(name='Group 1')
    assert group.name == 'Group 1'

def test_create_course():
    course = Course(title='Python Course', description='Learn Python')
    assert course.title == 'Python Course'
    assert course.description == 'Learn Python'

def test_user_from_db_row():
    row = {
        'id': 1,
        'email': 'row@example.com',
        'password_hash': 'hash',
        'name': 'Row User',
        'role': 'teacher',
        'group_id': None
    }
    user = User.from_db_row(row)
    assert user.id == 1
    assert user.email == 'row@example.com'
    assert user.name == 'Row User'
    assert user.role == 'teacher'
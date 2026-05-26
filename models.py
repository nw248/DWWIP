from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    group_id = db.Column(db.Integer, db.ForeignKey('groups.id'), nullable=True)
    
    assignments = db.relationship('Assignment', backref='student', lazy=True)
    # Связь с курсами (для преподавателей)
    courses = db.relationship('Course', secondary='teacher_course', back_populates='teachers')
    
    @property
    def password(self):
        raise AttributeError('Password is not readable')
    
    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    @staticmethod
    def from_db_row(row):
        """Создаёт объект User из строки БД без привязки к сессии"""
        user = User(
            email=row['email'],
            name=row['name'],
            role=row['role'],
            group_id=row['group_id']
        )
        user.id = row['id']
        user.password_hash = row['password_hash']
        return user

class Group(db.Model):
    __tablename__ = 'groups'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    
    students = db.relationship('User', backref='group', lazy=True)
    courses = db.relationship('Course', secondary='group_course', backref='groups')
    group_lessons = db.relationship('GroupLesson', backref='group', lazy=True, cascade='all, delete-orphan')

class Course(db.Model):
    __tablename__ = 'courses'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    lessons = db.relationship('Lesson', backref='course', lazy=True, cascade='all, delete-orphan')
    # Связь с преподавателями
    teachers = db.relationship('User', secondary='teacher_course', back_populates='courses')

class Lesson(db.Model):
    __tablename__ = 'lessons'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    lesson_type = db.Column(db.String(20), default='lecture')
    files = db.Column(db.JSON, default=list)  # JSON массив имён файлов
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    assignments = db.relationship('Assignment', backref='lesson', lazy=True, cascade='all, delete-orphan')
    questions = db.relationship('Question', backref='lesson', lazy=True, cascade='all, delete-orphan')
    group_lessons = db.relationship('GroupLesson', backref='lesson', lazy=True, cascade='all, delete-orphan')

class GroupLesson(db.Model):
    __tablename__ = 'group_lessons'
    
    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey('groups.id'), nullable=False)
    lesson_id = db.Column(db.Integer, db.ForeignKey('lessons.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (db.UniqueConstraint('group_id', 'lesson_id', name='unique_group_lesson'),)

class Question(db.Model):
    __tablename__ = 'questions'
    
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False)
    options = db.Column(db.JSON, nullable=False)
    correct_answers = db.Column(db.JSON, nullable=False)
    lesson_id = db.Column(db.Integer, db.ForeignKey('lessons.id'), nullable=False)
    
    test_answers = db.relationship('TestAnswer', backref='question', lazy=True, cascade='all, delete-orphan')

class Assignment(db.Model):
    __tablename__ = 'assignments'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    lesson_id = db.Column(db.Integer, db.ForeignKey('lessons.id'), nullable=False)
    answer_text = db.Column(db.Text, nullable=True)
    answer_file = db.Column(db.String(200), nullable=True)
    score = db.Column(db.Integer, nullable=True)
    feedback = db.Column(db.Text, nullable=True)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    test_answers = db.relationship('TestAnswer', backref='assignment', lazy=True, cascade='all, delete-orphan')

class TestAnswer(db.Model):
    __tablename__ = 'test_answers'
    
    id = db.Column(db.Integer, primary_key=True)
    assignment_id = db.Column(db.Integer, db.ForeignKey('assignments.id'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('questions.id'), nullable=False)
    answer = db.Column(db.String(1), nullable=False)
    is_correct = db.Column(db.Boolean, default=False)

# Связующие таблицы
teacher_course = db.Table('teacher_course',
    db.Column('teacher_id', db.Integer, db.ForeignKey('users.id')),
    db.Column('course_id', db.Integer, db.ForeignKey('courses.id'))
)

group_course = db.Table('group_course',
    db.Column('group_id', db.Integer, db.ForeignKey('groups.id')),
    db.Column('course_id', db.Integer, db.ForeignKey('courses.id'))
)
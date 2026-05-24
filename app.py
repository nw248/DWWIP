from flask import Flask, request, jsonify, session
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from models import db, User, Group, Course, Lesson, Question, Assignment, TestAnswer, GroupLesson, teacher_course, group_course
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
import os
from datetime import datetime, timedelta
import jwt
import psycopg2
from psycopg2.extras import RealDictCursor
import re
import os
import json
import subprocess
import glob

def validate_password(password):
    if len(password) < 8:
        return False, "Пароль должен содержать минимум 8 символов"
    if not re.search(r'[A-Z]', password):
        return False, "Пароль должен содержать хотя бы одну заглавную букву"
    if not re.search(r'[!@#$%^&*()_+\-=\[\]{};:""\\|,.<>\/?]', password):
        return False, "Пароль должен содержать хотя бы один специальный символ"
    return True, "OK"

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-change-in-production'
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:123@localhost/distance_learning'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# CORS для Vue.js (порт 5173)
CORS(app, origins=['http://localhost:5173'], supports_credentials=True)

db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = None

# Конфигурация базы данных для сырых SQL-запросов
DB_CONFIG = {
    'host': 'localhost',
    'database': 'distance_learning',
    'user': 'postgres',
    'password': '123'
}

def get_db_connection():
    conn = psycopg2.connect(**DB_CONFIG)
    conn.autocommit = False
    return conn

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ============ АУТЕНТИФИКАЦИЯ ============

@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    
    user = User.query.filter_by(email=email).first()
    if user and check_password_hash(user.password_hash, password):
        login_user(user)
        return jsonify({
            'success': True,
            'user': {
                'id': user.id,
                'name': user.name,
                'email': user.email,
                'role': user.role,
                'group_id': user.group_id
            }
        })
    return jsonify({'success': False, 'message': 'Неверный email или пароль'}), 401

@app.route('/api/logout', methods=['POST'])
@login_required
def api_logout():
    logout_user()
    return jsonify({'success': True})

@app.route('/api/me', methods=['GET'])
@login_required
def api_me():
    return jsonify({
        'id': current_user.id,
        'name': current_user.name,
        'email': current_user.email,
        'role': current_user.role,
        'group_id': current_user.group_id
    })

# ============ КУРСЫ ============

@app.route('/api/courses', methods=['GET'])
@login_required
def api_get_courses():
    print(f"DEBUG: current_user.id={current_user.id}, role={current_user.role}")
    
    # Для администратора — показываем все курсы
    if current_user.role == 'admin':
        courses = Course.query.all()
        return jsonify([{
            'id': c.id,
            'title': c.title,
            'description': c.description,
            'lessons_count': len(c.lessons),
            'created_at': c.created_at.isoformat() if c.created_at else None
        } for c in courses])
    
    elif current_user.role == 'teacher':
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("""
            SELECT c.id, c.title, c.description, c.created_at,
                   COUNT(l.id) as lessons_count
            FROM courses c
            JOIN teacher_course tc ON c.id = tc.course_id
            LEFT JOIN lessons l ON c.id = l.course_id
            WHERE tc.teacher_id = %s
            GROUP BY c.id
            ORDER BY c.created_at DESC
        """, (current_user.id,))
        courses = cur.fetchall()
        cur.close()
        conn.close()
        
        return jsonify([{
            'id': c['id'],
            'title': c['title'],
            'description': c['description'],
            'lessons_count': c['lessons_count'],
            'created_at': c['created_at'].isoformat() if c['created_at'] else None
        } for c in courses])
        
    elif current_user.role == 'student' and current_user.group_id:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("""
            SELECT c.id, c.title, c.description, c.created_at,
                   COUNT(l.id) as lessons_count
            FROM courses c
            JOIN group_course gc ON c.id = gc.course_id
            LEFT JOIN lessons l ON c.id = l.course_id
            WHERE gc.group_id = %s
            GROUP BY c.id
            ORDER BY c.created_at DESC
        """, (current_user.group_id,))
        courses = cur.fetchall()
        cur.close()
        conn.close()
        
        return jsonify([{
            'id': c['id'],
            'title': c['title'],
            'description': c['description'],
            'lessons_count': c['lessons_count'],
            'created_at': c['created_at'].isoformat() if c['created_at'] else None
        } for c in courses])
    else:
        return jsonify([])

@app.route('/api/admin/courses', methods=['GET'])
@login_required
def api_admin_get_courses():
    if current_user.role != 'admin':
        return jsonify({'error': 'Доступ запрещен'}), 403
    
    courses = Course.query.all()
    return jsonify([{
        'id': c.id,
        'title': c.title,
        'description': c.description,
        'lessons_count': len(c.lessons),
        'created_at': c.created_at.isoformat() if c.created_at else None,
        'teachers': ', '.join([t.name for t in c.teachers])
    } for c in courses])

@app.route('/api/courses', methods=['POST'])
@login_required
def api_create_course():
    if current_user.role not in ['admin', 'teacher']:
        return jsonify({'error': 'Доступ запрещен'}), 403
    
    data = request.get_json()
    title = data.get('title')
    description = data.get('description')
    
    if not title:
        return jsonify({'error': 'Название курса обязательно'}), 400
    
    course = Course(title=title, description=description)
    db.session.add(course)
    db.session.flush()
    
    if current_user.role == 'teacher':
        course.teachers.append(current_user)
    elif current_user.role == 'admin':
        teacher_ids = data.get('teacher_ids', [])
        for tid in teacher_ids:
            teacher = User.query.get(tid)
            if teacher and teacher.role == 'teacher':
                course.teachers.append(teacher)
    
    db.session.commit()
    return jsonify({'success': True, 'course_id': course.id})

@app.route('/api/courses/<int:course_id>', methods=['DELETE'])
@login_required
def api_delete_course(course_id):
    if current_user.role not in ['admin', 'teacher']:
        return jsonify({'error': 'Доступ запрещен'}), 403
    
    course = Course.query.get_or_404(course_id)
    
    if current_user.role == 'teacher' and course not in current_user.courses:
        return jsonify({'error': 'У вас нет доступа'}), 403
    
    db.session.delete(course)
    db.session.commit()
    return jsonify({'success': True})

@app.route('/api/courses/<int:course_id>', methods=['GET'])
@login_required
def api_get_course(course_id):
    course = Course.query.get_or_404(course_id)
    return jsonify({
        'id': course.id,
        'title': course.title,
        'description': course.description,
        'created_at': course.created_at.isoformat() if course.created_at else None
    })

@app.route('/api/courses/<int:course_id>/groups', methods=['GET'])
@login_required
def api_get_course_groups(course_id):
    course = Course.query.get_or_404(course_id)
    
    groups_data = []
    for group in course.groups:
        groups_data.append({
            'id': group.id,
            'name': group.name,
            'students_count': len(group.students),
            'lessons_count': len(group.group_lessons)
        })
    
    return jsonify(groups_data)

@app.route('/api/courses/<int:course_id>/groups', methods=['POST'])
@login_required
def api_add_groups_to_course(course_id):
    if current_user.role not in ['admin', 'teacher']:
        return jsonify({'error': 'Доступ запрещен'}), 403
    
    course = Course.query.get_or_404(course_id)
    
    if current_user.role == 'teacher' and course not in current_user.courses:
        return jsonify({'error': 'У вас нет доступа к этому курсу'}), 403
    
    data = request.get_json()
    group_ids = data.get('groups', [])
    
    course.groups = []
    for gid in group_ids:
        group = Group.query.get(gid)
        if group:
            course.groups.append(group)
    
    db.session.commit()
    return jsonify({'success': True})

@app.route('/api/courses/<int:course_id>/teachers', methods=['GET'])
@login_required
def api_get_course_teachers(course_id):
    course = Course.query.get_or_404(course_id)
    return jsonify([{
        'id': t.id,
        'name': t.name,
        'email': t.email
    } for t in course.teachers])

@app.route('/api/courses/<int:course_id>', methods=['PUT'])
@login_required
def api_update_course(course_id):
    if current_user.role not in ['admin', 'teacher']:
        return jsonify({'error': 'Доступ запрещен'}), 403
    
    course = Course.query.get_or_404(course_id)
    
    if current_user.role == 'teacher' and course not in current_user.courses:
        return jsonify({'error': 'У вас нет доступа'}), 403
    
    data = request.get_json()
    
    course.title = data.get('title', course.title)
    course.description = data.get('description', course.description)
    
    if current_user.role == 'admin' and data.get('teacher_ids') is not None:
        course.teachers = []
        for tid in data['teacher_ids']:
            teacher = User.query.get(tid)
            if teacher and teacher.role == 'teacher':
                course.teachers.append(teacher)
    
    db.session.commit()
    return jsonify({'success': True})

# ============ ГРУППЫ ============

@app.route('/api/groups', methods=['GET'])
@login_required
def api_get_groups():
    # Разрешаем доступ и преподавателям, и администраторам
    if current_user.role not in ['admin', 'teacher']:
        return jsonify({'error': 'Доступ запрещен'}), 403
    
    groups = Group.query.all()
    return jsonify([{
        'id': g.id,
        'name': g.name,
        'students_count': len(g.students)
    } for g in groups])

@app.route('/api/groups/<int:group_id>', methods=['GET'])
@login_required
def api_get_group(group_id):
    group = Group.query.get_or_404(group_id)
    return jsonify({
        'id': group.id,
        'name': group.name,
        'students_count': len(group.students)
    })

@app.route('/api/groups', methods=['POST'])
@login_required
def api_create_group():
    if current_user.role != 'admin':
        return jsonify({'error': 'Доступ запрещен'}), 403
    
    data = request.get_json()
    name = data.get('name')
    
    if not name:
        return jsonify({'error': 'Название группы обязательно'}), 400
    
    group = Group(name=name)
    db.session.add(group)
    db.session.commit()
    return jsonify({'success': True, 'group_id': group.id})

@app.route('/api/groups/<int:group_id>', methods=['DELETE'])
@login_required
def api_delete_group(group_id):
    if current_user.role != 'admin':
        return jsonify({'error': 'Доступ запрещен'}), 403
    
    group = Group.query.get_or_404(group_id)
    
    for student in group.students:
        student.group_id = None
    
    db.session.delete(group)
    db.session.commit()
    return jsonify({'success': True})

@app.route('/api/lessons/<int:lesson_id>/update', methods=['POST'])
@login_required
def api_update_assignment(lesson_id):
    if current_user.role != 'student':
        return jsonify({'error': 'Доступ запрещен'}), 403
    
    lesson = Lesson.query.get_or_404(lesson_id)
    
    group_lesson = GroupLesson.query.filter_by(
        group_id=current_user.group_id, 
        lesson_id=lesson_id
    ).first()
    
    if not group_lesson:
        return jsonify({'error': 'Урок не доступен вашей группе'}), 403
    
    answer_text = request.form.get('answer_text', '')
    answer_file = request.files.get('answer_file')
    
    filename = None
    if answer_file and answer_file.filename:
        from werkzeug.utils import secure_filename
        filename = secure_filename(f"{current_user.id}_{lesson_id}_{answer_file.filename}")
        answer_file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    
    existing = Assignment.query.filter_by(
        student_id=current_user.id,
        lesson_id=lesson_id
    ).first()
    
    if existing:
        existing.answer_text = answer_text
        if filename:
            existing.answer_file = filename
        existing.submitted_at = datetime.utcnow()
        db.session.commit()
        return jsonify({'success': True, 'message': 'Ответ обновлён'})
    
    return jsonify({'error': 'Ответ не найден'}), 404

# ============ ПОЛЬЗОВАТЕЛИ ============

@app.route('/api/users', methods=['GET'])
@login_required
def api_get_users():
    if current_user.role != 'admin':
        return jsonify({'error': 'Доступ запрещен'}), 403
    
    users = User.query.all()
    return jsonify([{
        'id': u.id,
        'name': u.name,
        'email': u.email,
        'role': u.role,
        'group_id': u.group_id,
        'group_name': u.group.name if u.group else None
    } for u in users])

@app.route('/api/users/<int:user_id>', methods=['GET'])
@login_required
def api_get_user(user_id):
    if current_user.role != 'admin':
        return jsonify({'error': 'Доступ запрещен'}), 403
    
    user = User.query.get_or_404(user_id)
    return jsonify({
        'id': user.id,
        'email': user.email,
        'name': user.name,
        'role': user.role,
        'group_id': user.group_id
    })

@app.route('/api/users', methods=['POST'])
@login_required
def api_create_user():
    if current_user.role != 'admin':
        return jsonify({'error': 'Доступ запрещен'}), 403
    
    data = request.get_json()
    
    # ВАЛИДАЦИЯ ПАРОЛЯ
    valid, msg = validate_password(data['password'])
    if not valid:
        return jsonify({'error': msg}), 400
    
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Пользователь с таким email уже существует'}), 400
    
    user = User(
        email=data['email'],
        password_hash=generate_password_hash(data['password']),
        name=data['name'],
        role=data['role'],
        group_id=data.get('group_id')
    )
    db.session.add(user)
    db.session.commit()
    return jsonify({'success': True, 'user_id': user.id})

@app.route('/api/users/<int:user_id>', methods=['PUT'])
@login_required
def api_update_user(user_id):
    if current_user.role != 'admin':
        return jsonify({'error': 'Доступ запрещен'}), 403
    
    user = User.query.get_or_404(user_id)
    data = request.get_json()
    
    if 'email' in data:
        existing = User.query.filter(User.email == data['email'], User.id != user_id).first()
        if existing:
            return jsonify({'error': 'Email уже используется'}), 400
        user.email = data['email']
    
    if data.get('new_password'):
        # ВАЛИДАЦИЯ НОВОГО ПАРОЛЯ
        valid, msg = validate_password(data['new_password'])
        if not valid:
            return jsonify({'error': msg}), 400
        user.password_hash = generate_password_hash(data['new_password'])
    
    db.session.commit()
    return jsonify({'success': True})

@app.route('/api/users/<int:user_id>', methods=['DELETE'])
@login_required
def api_delete_user(user_id):
    if current_user.role != 'admin':
        return jsonify({'error': 'Доступ запрещен'}), 403
    
    user = User.query.get_or_404(user_id)
    if user.role == 'admin':
        return jsonify({'error': 'Нельзя удалить администратора'}), 400
    
    db.session.delete(user)
    db.session.commit()
    return jsonify({'success': True})

@app.route('/api/admin/backup', methods=['POST'])
@login_required
def api_backup_database():
    if current_user.role != 'admin':
        return jsonify({'error': 'Доступ запрещен'}), 403
    
    try:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f"backup_{timestamp}.sql"
        backup_path = os.path.join('backups', backup_filename)
        
        os.makedirs('backups', exist_ok=True)
        
        # Создаём бэкап через psycopg2 (без внешних команд)
        conn = get_db_connection()
        cur = conn.cursor()
        
        with open(backup_path, 'w', encoding='utf-8') as f:
            # Получаем все таблицы
            cur.execute("""
                SELECT table_name FROM information_schema.tables 
                WHERE table_schema = 'public' 
                ORDER BY table_name
            """)
            tables = cur.fetchall()
            
            for table in tables:
                table_name = table[0]
                # Получаем структуру таблицы
                cur.execute(f"SELECT column_name, data_type FROM information_schema.columns WHERE table_name = '{table_name}' ORDER BY ordinal_position")
                columns = cur.fetchall()
                
                # Получаем данные
                cur.execute(f"SELECT * FROM {table_name}")
                rows = cur.fetchall()
                
                f.write(f"-- Таблица: {table_name}\n")
                for row in rows:
                    f.write(f"INSERT INTO {table_name} VALUES ({','.join([str(x) if x else 'NULL' for x in row])});\n")
                f.write("\n")
        
        cur.close()
        conn.close()
        
        return jsonify({
            'success': True, 
            'message': f'Резервная копия создана: {backup_filename}',
            'filename': backup_filename
        })
        
    except Exception as e:
        print(f"Исключение: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/admin/backup/download/<filename>', methods=['GET'])
@login_required
def api_download_backup(filename):
    if current_user.role != 'admin':
        return jsonify({'error': 'Доступ запрещен'}), 403
    
    from flask import send_file
    backup_path = os.path.join('backups', filename)
    
    if not os.path.exists(backup_path):
        return jsonify({'error': 'Файл не найден'}), 404
    
    return send_file(backup_path, as_attachment=True, download_name=filename)

@app.route('/api/admin/backups', methods=['GET'])
@login_required
def api_list_backups():
    if current_user.role != 'admin':
        return jsonify({'error': 'Доступ запрещен'}), 403
    
    backup_files = glob.glob('backups/backup_*.sql')
    backups = []
    for file in backup_files:
        name = os.path.basename(file)
        date_str = name.replace('backup_', '').replace('.sql', '')
        date = datetime.strptime(date_str, '%Y%m%d_%H%M%S').strftime('%d.%m.%Y %H:%M:%S')
        backups.append({'name': name, 'date': date})
    
    # Сортируем по дате (новые сверху)
    backups.sort(key=lambda x: x['name'], reverse=True)
    
    return jsonify(backups)

# ============ УРОКИ ============

@app.route('/api/lessons/<int:lesson_id>', methods=['GET'])
@login_required
def api_get_lesson(lesson_id):
    lesson = Lesson.query.get_or_404(lesson_id)
    return jsonify({
        'id': lesson.id,
        'title': lesson.title,
        'content': lesson.content,
        'lesson_type': lesson.lesson_type,
        'files': lesson.files if hasattr(lesson, 'files') else [],
        'course_id': lesson.course_id,
        'created_at': lesson.created_at.isoformat() if lesson.created_at else None
    })

@app.route('/api/courses/<int:course_id>/groups/<int:group_id>/lessons', methods=['GET'])
@login_required
def api_get_lessons(course_id, group_id):
    group_lessons = GroupLesson.query.filter_by(group_id=group_id).all()
    lesson_ids = [gl.lesson_id for gl in group_lessons]
    lessons = Lesson.query.filter(Lesson.id.in_(lesson_ids), Lesson.course_id == course_id).all()
    
    return jsonify([{
        'id': l.id,
        'title': l.title,
        'content': l.content[:200],
        'lesson_type': l.lesson_type,
        'files': l.files if hasattr(l, 'files') else [],
        'created_at': l.created_at.isoformat() if l.created_at else None
    } for l in lessons])

@app.route('/api/courses/<int:course_id>/groups/<int:group_id>/lessons/progress', methods=['GET'])
@login_required
def api_get_lessons_progress(course_id, group_id):
    if current_user.role != 'teacher':
        return jsonify({'error': 'Доступ запрещен'}), 403
    
    group_lessons = GroupLesson.query.filter_by(group_id=group_id).all()
    lesson_ids = [gl.lesson_id for gl in group_lessons]
    lessons = Lesson.query.filter(Lesson.id.in_(lesson_ids), Lesson.course_id == course_id).all()
    
    students = User.query.filter_by(group_id=group_id, role='student').all()
    total_students = len(students)
    
    result = []
    for lesson in lessons:
        completed = Assignment.query.filter(
            Assignment.lesson_id == lesson.id,
            Assignment.student_id.in_([s.id for s in students])
        ).count()
        
        progress = 0
        if total_students > 0:
            progress = int((completed / total_students) * 100)
        
        result.append({
            'id': lesson.id,
            'title': lesson.title,
            'content': lesson.content[:100],
            'lesson_type': lesson.lesson_type,
            'progress': progress,
            'completed': completed,
            'total': total_students
        })
    
    return jsonify(result)

@app.route('/api/courses/<int:course_id>/groups/<int:group_id>/lessons', methods=['POST'])
@login_required
def api_create_lesson(course_id, group_id):
    if current_user.role not in ['admin', 'teacher']:
        return jsonify({'error': 'Доступ запрещен'}), 403
    
    title = request.form.get('title')
    content = request.form.get('content')
    lesson_type = request.form.get('lesson_type')
    
    # Сохраняем файлы
    files = request.files.getlist('files')
    filenames = []
    for file in files:
        if file and file.filename:
            filename = secure_filename(f"{current_user.id}_{course_id}_{group_id}_{file.filename}")
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            filenames.append(filename)
    
    lesson = Lesson(
        title=title,
        content=content,
        lesson_type=lesson_type,
        files=filenames,  # Сохраняем список имён файлов
        course_id=course_id
    )
    db.session.add(lesson)
    db.session.flush()
    
    group_lesson = GroupLesson(group_id=group_id, lesson_id=lesson.id)
    db.session.add(group_lesson)
    
    if lesson_type == 'test':
        questions_data = json.loads(request.form.get('questions', '[]'))
        for q in questions_data:
            question = Question(
                text=q['text'],
                options=q['options'],
                correct_answers=q['correct_answers'],
                lesson_id=lesson.id
            )
            db.session.add(question)
    
    db.session.commit()
    return jsonify({'success': True, 'lesson_id': lesson.id})

@app.route('/api/lessons/<int:lesson_id>', methods=['DELETE'])
@login_required
def api_delete_lesson(lesson_id):
    if current_user.role not in ['admin', 'teacher']:
        return jsonify({'error': 'Доступ запрещен'}), 403
    
    lesson = Lesson.query.get_or_404(lesson_id)
    
    # Проверка прав для преподавателя
    if current_user.role == 'teacher':
        course = lesson.course
        if course not in current_user.courses:
            return jsonify({'error': 'У вас нет доступа к этому курсу'}), 403
    
    try:
        # Удаляем связи группы с уроком
        GroupLesson.query.filter_by(lesson_id=lesson_id).delete()
        
        # Удаляем вопросы теста
        Question.query.filter_by(lesson_id=lesson_id).delete()
        
        # Удаляем ответы на тесты и сами задания
        assignments = Assignment.query.filter_by(lesson_id=lesson_id).all()
        for assignment in assignments:
            TestAnswer.query.filter_by(assignment_id=assignment.id).delete()
            db.session.delete(assignment)
        
        db.session.delete(lesson)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Урок удалён'})
    except Exception as e:
        db.session.rollback()
        print(f"Ошибка удаления урока: {e}")
        return jsonify({'error': str(e)}), 500

# ============ ЗАДАНИЯ ============

@app.route('/api/lessons/<int:lesson_id>/submit', methods=['POST'])
@login_required
def api_submit_assignment(lesson_id):
    if current_user.role != 'student':
        return jsonify({'error': 'Доступ запрещен'}), 403
    
    lesson = Lesson.query.get_or_404(lesson_id)
    
    group_lesson = GroupLesson.query.filter_by(
        group_id=current_user.group_id, 
        lesson_id=lesson_id
    ).first()
    
    if not group_lesson:
        return jsonify({'error': 'Урок не доступен вашей группе'}), 403
    
    answer_text = request.form.get('answer_text', '')
    answer_file = request.files.get('answer_file')
    
    filename = None
    if answer_file and answer_file.filename:
        filename = secure_filename(f"{current_user.id}_{lesson_id}_{answer_file.filename}")
        answer_file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    
    existing = Assignment.query.filter_by(
        student_id=current_user.id,
        lesson_id=lesson_id
    ).first()
    
    if existing:
        existing.answer_text = answer_text
        existing.answer_file = filename
        existing.submitted_at = datetime.utcnow()
    else:
        assignment = Assignment(
            student_id=current_user.id,
            lesson_id=lesson_id,
            answer_text=answer_text,
            answer_file=filename
        )
        db.session.add(assignment)
    
    db.session.commit()
    return jsonify({'success': True, 'message': 'Ответ отправлен'})

@app.route('/api/lessons/<int:lesson_id>/groups/<int:group_id>/assignments', methods=['GET'])
@login_required
def api_get_assignments(lesson_id, group_id):
    if current_user.role != 'teacher':
        return jsonify({'error': 'Доступ запрещен'}), 403
    
    assignments = Assignment.query.filter_by(lesson_id=lesson_id).all()
    result = []
    for a in assignments:
        if a.student.group_id == group_id:
            result.append({
                'id': a.id,
                'student_name': a.student.name,
                'answer_text': a.answer_text,
                'answer_file': a.answer_file,
                'score': a.score,
                'feedback': a.feedback,
                'submitted_at': a.submitted_at.isoformat() if a.submitted_at else None
            })
    
    return jsonify(result)

@app.route('/api/assignments/<int:assignment_id>/grade', methods=['POST'])
@login_required
def api_grade_assignment(assignment_id):
    if current_user.role != 'teacher':
        return jsonify({'error': 'Доступ запрещен'}), 403
    
    assignment = Assignment.query.get_or_404(assignment_id)
    data = request.get_json()
    
    assignment.score = data.get('score')
    assignment.feedback = data.get('feedback')
    db.session.commit()
    
    return jsonify({'success': True})

@app.route('/api/assignments/lesson/<int:lesson_id>', methods=['GET'])
@login_required
def api_get_assignment_by_lesson(lesson_id):
    if current_user.role != 'student':
        return jsonify({'error': 'Доступ запрещен'}), 403
    
    assignment = Assignment.query.filter_by(
        student_id=current_user.id,
        lesson_id=lesson_id
    ).first()
    
    if not assignment:
        return jsonify(None), 200
    
    return jsonify({
        'id': assignment.id,
        'answer_text': assignment.answer_text,
        'answer_file': assignment.answer_file,
        'score': assignment.score,
        'feedback': assignment.feedback,
        'submitted_at': assignment.submitted_at.isoformat() if assignment.submitted_at else None
    })

# Добавьте этот маршрут для раздачи файлов из папки uploads
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    from flask import send_from_directory
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# ============ ТЕСТЫ ============

@app.route('/api/lessons/<int:lesson_id>/test/start', methods=['GET'])
@login_required
def api_start_test(lesson_id):
    lesson = Lesson.query.get_or_404(lesson_id)
    if lesson.lesson_type != 'test':
        return jsonify({'error': 'Это не тест'}), 400
    
    questions = lesson.questions
    return jsonify([{
        'id': q.id,
        'text': q.text,
        'option_a': q.option_a,
        'option_b': q.option_b,
        'option_c': q.option_c,
        'option_d': q.option_d
    } for q in questions])

@app.route('/api/lessons/<int:lesson_id>/test/submit', methods=['POST'])
@login_required
def api_submit_test(lesson_id):
    lesson = Lesson.query.get_or_404(lesson_id)
    data = request.get_json()
    answers = data.get('answers', {})
    
    questions = lesson.questions
    score = 0
    total = len(questions)
    
    assignment = Assignment.query.filter_by(
        student_id=current_user.id,
        lesson_id=lesson_id
    ).first()
    
    if not assignment:
        assignment = Assignment(student_id=current_user.id, lesson_id=lesson_id)
        db.session.add(assignment)
        db.session.flush()
    
    for q in questions:
        answer = answers.get(str(q.id))
        if answer:
            is_correct = (answer == q.correct_answer)
            if is_correct:
                score += 1
            
            test_answer = TestAnswer(
                assignment_id=assignment.id,
                question_id=q.id,
                answer=answer,
                is_correct=is_correct
            )
            db.session.add(test_answer)
    
    assignment.score = score
    assignment.feedback = f"Результат: {score} из {total} правильных ответов"
    db.session.commit()
    
    return jsonify({'score': score, 'total': total, 'feedback': assignment.feedback})

# ============ ЗАПУСК ============

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5000)
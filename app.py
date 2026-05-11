from flask import Flask, render_template, redirect, url_for, flash, request, send_from_directory
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from models import db, User, Group, Course, Lesson, Question, Assignment, TestAnswer, GroupLesson, teacher_course, group_course
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this-in-production'

# Конфигурация базы данных PostgreSQL
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

app.config['SQLALCHEMY_DATABASE_URI'] = f"postgresql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}/{DB_CONFIG['database']}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cur.execute("SELECT * FROM users WHERE id = %s", (user_id,))
        user_data = cur.fetchone()
        if user_data:
            return User.from_db_row(user_data)
        return None
    except Exception as e:
        print(f"Ошибка загрузки пользователя: {e}")
        return None
    finally:
        cur.close()
        conn.close()

# Создание таблиц
with app.app_context():
    db.create_all()
    print("Таблицы созданы")

# ====================== МАРШРУТЫ ======================

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        try:
            cur.execute("SELECT * FROM users WHERE email = %s", (email,))
            user_data = cur.fetchone()
            
            if user_data and check_password_hash(user_data['password_hash'], password):
                user = User.from_db_row(user_data)
                login_user(user)
                return redirect(url_for('index'))
            else:
                flash('Неверный email или пароль', 'danger')
        except Exception as e:
            flash(f'Ошибка при входе: {str(e)}', 'danger')
        finally:
            cur.close()
            conn.close()
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Вы вышли из системы', 'info')
    return redirect('/login')

@app.route('/')
@login_required
def index():
    if current_user.role == 'admin':
        return redirect(url_for('admin_dashboard'))
    elif current_user.role == 'teacher':
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        try:
            cur.execute("""
                SELECT c.id, c.title, c.description, c.created_at,
                       COUNT(l.id) as lessons_count
                FROM courses c
                JOIN teacher_course tc ON c.id = tc.course_id
                LEFT JOIN lessons l ON c.id = l.course_id
                WHERE tc.teacher_id = %s
                GROUP BY c.id, c.title, c.description, c.created_at
                ORDER BY c.created_at DESC
            """, (current_user.id,))
            courses_data = cur.fetchall()
            
            # Преобразуем в список словарей для шаблона
            courses = []
            for row in courses_data:
                courses.append({
                    'id': row['id'],
                    'title': row['title'],
                    'description': row['description'],
                    'created_at': row['created_at'],
                    'lessons_count': row['lessons_count']
                })
            
            print(f"DEBUG: Teacher {current_user.name} has {len(courses)} courses")
            for c in courses:
                print(f"  - {c['title']} (id={c['id']}, lessons={c['lessons_count']})")
                
        except Exception as e:
            print(f"DEBUG: Ошибка загрузки курсов: {e}")
            courses = []
        finally:
            cur.close()
            conn.close()
        
        return render_template('index_teacher.html', courses=courses, role='teacher')
    else:
        # Студент
        if not current_user.group_id:
            flash('Вы не прикреплены ни к одной группе. Обратитесь к администратору.', 'warning')
            return render_template('index_student.html', courses=[], role='student')
        
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        try:
            cur.execute("""
                SELECT c.id, c.title, c.description, c.created_at,
                       COUNT(DISTINCT l.id) as lessons_count
                FROM courses c
                JOIN group_course gc ON c.id = gc.course_id
                LEFT JOIN group_lessons gl ON gc.group_id = gl.group_id
                LEFT JOIN lessons l ON gl.lesson_id = l.id AND l.course_id = c.id
                WHERE gc.group_id = %s
                GROUP BY c.id, c.title, c.description, c.created_at
                ORDER BY c.created_at DESC
            """, (current_user.group_id,))
            courses_data = cur.fetchall()
            
            courses = []
            for row in courses_data:
                courses.append({
                    'id': row['id'],
                    'title': row['title'],
                    'description': row['description'],
                    'created_at': row['created_at'],
                    'lessons_count': row['lessons_count']
                })
            
            print(f"DEBUG: Student {current_user.name} (group_id={current_user.group_id}) has {len(courses)} courses")
        except Exception as e:
            print(f"DEBUG: Ошибка загрузки курсов: {e}")
            courses = []
        finally:
            cur.close()
            conn.close()
        
        return render_template('index_student.html', courses=courses, role='student')
@app.route('/create_course', methods=['GET', 'POST'])
@login_required
def create_course():
    if current_user.role != 'teacher':
        flash('Доступ запрещен. Только преподаватели могут создавать курсы', 'danger')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        
        if not title:
            flash('Название курса обязательно', 'danger')
            return redirect(url_for('create_course'))
        
        conn = get_db_connection()
        cur = conn.cursor()
        
        try:
            # 1. Создаём курс
            cur.execute("""
                INSERT INTO courses (title, description, created_at)
                VALUES (%s, %s, %s)
                RETURNING id
            """, (title, description, datetime.utcnow()))
            
            course_id = cur.fetchone()[0]
            print(f"DEBUG: Создан курс id={course_id}, title={title}")
            
            # 2. Добавляем связь преподаватель-курс
            cur.execute("""
                INSERT INTO teacher_course (teacher_id, course_id)
                VALUES (%s, %s)
            """, (current_user.id, course_id))
            
            conn.commit()
            print(f"DEBUG: Связь добавлена: teacher={current_user.id}, course={course_id}")
            
            flash(f'Курс "{title}" успешно создан', 'success')
            
        except Exception as e:
            conn.rollback()
            print(f"DEBUG: Ошибка: {e}")
            flash(f'Ошибка при создании курса: {str(e)}', 'danger')
        finally:
            cur.close()
            conn.close()
        
        return redirect(url_for('index'))
    
    return render_template('create_course.html')

@app.route('/course/<int:course_id>')
@login_required
def course(course_id):
    if current_user.role == 'teacher':
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        try:
            cur.execute("""
                SELECT * FROM teacher_course 
                WHERE teacher_id = %s AND course_id = %s
            """, (current_user.id, course_id))
            has_access = cur.fetchone()
            
            if not has_access:
                flash('У вас нет доступа к этому курсу', 'danger')
                return redirect(url_for('index'))
        finally:
            cur.close()
            conn.close()
        
        course = Course.query.get_or_404(course_id)
        groups = course.groups
        return render_template('course_teacher.html', course=course, groups=groups)
    else:
        if not current_user.group_id:
            flash('Вы не прикреплены ни к одной группе', 'danger')
            return redirect(url_for('index'))
        
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        try:
            cur.execute("""
                SELECT * FROM group_course 
                WHERE group_id = %s AND course_id = %s
            """, (current_user.group_id, course_id))
            has_access = cur.fetchone()
            
            if not has_access:
                flash('У вас нет доступа к этому курсу', 'danger')
                return redirect(url_for('index'))
        finally:
            cur.close()
            conn.close()
        
        course = Course.query.get_or_404(course_id)
        
        group_lessons = GroupLesson.query.filter_by(group_id=current_user.group_id).all()
        lesson_ids = [gl.lesson_id for gl in group_lessons]
        lessons = Lesson.query.filter(Lesson.id.in_(lesson_ids), Lesson.course_id == course.id).all()
        
        return render_template('course_student.html', course=course, lessons=lessons)
    
@app.route('/admin/delete_course/<int:course_id>', methods=['POST'])
@login_required
def delete_course(course_id):
    if current_user.role != 'admin':
        flash('Доступ запрещен', 'danger')
        return redirect(url_for('index'))
    
    course = Course.query.get_or_404(course_id)
    course_title = course.title
    
    # Удаляем связи teacher_course
    db.session.execute(teacher_course.delete().where(teacher_course.c.course_id == course_id))
    
    # Удаляем связи group_course
    db.session.execute(group_course.delete().where(group_course.c.course_id == course_id))
    
    # Удаляем связи group_lessons и сами уроки каскадно удалятся
    db.session.delete(course)
    db.session.commit()
    
    flash(f'Курс "{course_title}" удален', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/course/delete/<int:course_id>', methods=['POST'])
@login_required
def delete_course_teacher(course_id):
    if current_user.role != 'teacher':
        flash('Доступ запрещен', 'danger')
        return redirect(url_for('index'))
    
    # Проверяем, что преподаватель имеет доступ к курсу
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cur.execute("""
            SELECT * FROM teacher_course 
            WHERE teacher_id = %s AND course_id = %s
        """, (current_user.id, course_id))
        has_access = cur.fetchone()
        
        if not has_access:
            flash('У вас нет доступа к этому курсу', 'danger')
            return redirect(url_for('index'))
    finally:
        cur.close()
        conn.close()
    
    course = Course.query.get_or_404(course_id)
    course_title = course.title
    
    # Удаляем связи teacher_course
    db.session.execute(teacher_course.delete().where(teacher_course.c.course_id == course_id))
    
    # Удаляем связи group_course
    db.session.execute(group_course.delete().where(group_course.c.course_id == course_id))
    
    # Удаляем связи group_lessons и сами уроки каскадно удалятся
    db.session.delete(course)
    db.session.commit()
    
    flash(f'Курс "{course_title}" удален', 'success')
    return redirect(url_for('index'))

@app.route('/course/<int:course_id>/add_students', methods=['GET', 'POST'])
@login_required
def add_students_to_course(course_id):
    if current_user.role != 'teacher':
        flash('Доступ запрещен', 'danger')
        return redirect(url_for('index'))
    
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cur.execute("""
            SELECT * FROM teacher_course 
            WHERE teacher_id = %s AND course_id = %s
        """, (current_user.id, course_id))
        has_access = cur.fetchone()
        
        if not has_access:
            flash('У вас нет доступа к этому курсу', 'danger')
            return redirect(url_for('index'))
    finally:
        cur.close()
        conn.close()
    
    course = Course.query.get_or_404(course_id)
    
    if request.method == 'POST':
        group_ids = request.form.getlist('groups')
        course.groups = []
        for group_id in group_ids:
            group = Group.query.get(int(group_id))
            if group:
                course.groups.append(group)
        db.session.commit()
        flash('Группы успешно добавлены к курсу', 'success')
        return redirect(url_for('course', course_id=course.id))
    
    all_groups = Group.query.all()
    current_groups = course.groups
    return render_template('add_students_to_course.html', course=course, all_groups=all_groups, current_groups=current_groups)

@app.route('/course/<int:course_id>/group/<int:group_id>')
@login_required
def course_group(course_id, group_id):
    if current_user.role != 'teacher':
        flash('Доступ запрещен', 'danger')
        return redirect(url_for('index'))
    
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cur.execute("""
            SELECT * FROM teacher_course 
            WHERE teacher_id = %s AND course_id = %s
        """, (current_user.id, course_id))
        has_access = cur.fetchone()
        
        if not has_access:
            flash('У вас нет доступа к этому курсу', 'danger')
            return redirect(url_for('index'))
    finally:
        cur.close()
        conn.close()
    
    course = Course.query.get_or_404(course_id)
    group = Group.query.get_or_404(group_id)
    
    if group not in course.groups:
        flash('Эта группа не добавлена к курсу', 'danger')
        return redirect(url_for('course', course_id=course.id))
    
    group_lessons = GroupLesson.query.filter_by(group_id=group.id).all()
    lesson_ids = [gl.lesson_id for gl in group_lessons]
    lessons = Lesson.query.filter(Lesson.id.in_(lesson_ids), Lesson.course_id == course.id).all()
    students = User.query.filter_by(group_id=group.id, role='student').all()
    
    return render_template('course_group.html', course=course, group=group, lessons=lessons, students=students)

@app.route('/course/<int:course_id>/group/<int:group_id>/add_lesson', methods=['GET', 'POST'])
@login_required
def add_lesson_to_group(course_id, group_id):
    if current_user.role != 'teacher':
        flash('Доступ запрещен', 'danger')
        return redirect(url_for('index'))
    
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cur.execute("""
            SELECT * FROM teacher_course 
            WHERE teacher_id = %s AND course_id = %s
        """, (current_user.id, course_id))
        has_access = cur.fetchone()
        
        if not has_access:
            flash('У вас нет доступа к этому курсу', 'danger')
            return redirect(url_for('index'))
    finally:
        cur.close()
        conn.close()
    
    course = Course.query.get_or_404(course_id)
    group = Group.query.get_or_404(group_id)
    
    if group not in course.groups:
        flash('Эта группа не добавлена к курсу', 'danger')
        return redirect(url_for('course', course_id=course.id))
    
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        lesson_type = request.form.get('lesson_type')
        
        lesson = Lesson(title=title, content=content, lesson_type=lesson_type, course_id=course.id)
        db.session.add(lesson)
        db.session.flush()
        
        group_lesson = GroupLesson(group_id=group.id, lesson_id=lesson.id)
        db.session.add(group_lesson)
        
        if lesson_type == 'test':
            questions_count = int(request.form.get('questions_count', 0))
            for i in range(questions_count):
                question_text = request.form.get(f'question_{i}_text')
                option_a = request.form.get(f'question_{i}_a')
                option_b = request.form.get(f'question_{i}_b')
                option_c = request.form.get(f'question_{i}_c')
                option_d = request.form.get(f'question_{i}_d')
                correct = request.form.get(f'question_{i}_correct')
                
                if question_text and option_a and correct:
                    question = Question(
                        text=question_text,
                        option_a=option_a,
                        option_b=option_b,
                        option_c=option_c,
                        option_d=option_d,
                        correct_answer=correct,
                        lesson_id=lesson.id
                    )
                    db.session.add(question)
        
        db.session.commit()
        flash(f'Урок "{title}" успешно добавлен для группы "{group.name}"', 'success')
        return redirect(url_for('course_group', course_id=course.id, group_id=group.id))
    
    return render_template('add_lesson_to_group.html', course=course, group=group)

@app.route('/group_lesson/<int:group_lesson_id>')
@login_required
def group_lesson(group_lesson_id):
    group_lesson = GroupLesson.query.get_or_404(group_lesson_id)
    lesson = group_lesson.lesson
    group = group_lesson.group
    course = lesson.course
    
    if current_user.role == 'teacher':
        # Проверяем доступ к курсу
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        try:
            cur.execute("""
                SELECT * FROM teacher_course 
                WHERE teacher_id = %s AND course_id = %s
            """, (current_user.id, course.id))
            has_access = cur.fetchone()
            
            if not has_access:
                flash('У вас нет доступа', 'danger')
                return redirect(url_for('index'))
        finally:
            cur.close()
            conn.close()
        
        assignments = Assignment.query.filter_by(lesson_id=lesson.id).all()
        group_assignments = [a for a in assignments if a.student.group_id == group.id]
        
        return render_template('group_lesson_teacher.html', 
                               lesson=lesson, course=course, 
                               group=group, assignments=group_assignments)
    else:
        # Студент
        if current_user.group_id != group.id:
            flash('У вас нет доступа', 'danger')
            return redirect(url_for('index'))
        
        assignment = Assignment.query.filter_by(
            student_id=current_user.id, 
            lesson_id=lesson.id
        ).first()
        
        if lesson.lesson_type == 'test':
            if assignment and assignment.test_answers:
                return render_template('group_lesson_student.html', 
                                       lesson=lesson, course=course, 
                                       group=group, assignment=assignment)
            else:
                return redirect(url_for('take_test', lesson_id=lesson.id, group_id=group.id))
        
        return render_template('group_lesson_student.html', 
                               lesson=lesson, course=course, 
                               group=group, assignment=assignment)

@app.route('/lesson/<int:lesson_id>/submit', methods=['POST'])
@login_required
def submit_assignment(lesson_id):
    if current_user.role != 'student':
        flash('Доступ запрещен', 'danger')
        return redirect(url_for('index'))
    
    lesson = Lesson.query.get_or_404(lesson_id)
    course = lesson.course
    
    # Проверяем, есть ли группа у студента
    if not current_user.group_id:
        flash('Вы не прикреплены ни к одной группе', 'danger')
        return redirect(url_for('index'))
    
    # Проверяем, есть ли доступ к курсу через группу (сырой SQL)
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cur.execute("""
            SELECT * FROM group_course 
            WHERE group_id = %s AND course_id = %s
        """, (current_user.group_id, course.id))
        has_access = cur.fetchone()
        
        if not has_access:
            flash('У вас нет доступа к этому курсу', 'danger')
            return redirect(url_for('index'))
    finally:
        cur.close()
        conn.close()
    
    # Проверяем, что урок назначен группе студента
    group_lesson = GroupLesson.query.filter_by(
        group_id=current_user.group_id, 
        lesson_id=lesson.id
    ).first()
    
    if not group_lesson:
        flash('Этот урок не доступен вашей группе', 'danger')
        return redirect(url_for('index'))
    
    answer_text = request.form.get('answer_text')
    answer_file = request.files.get('answer_file')
    
    filename = None
    if answer_file and answer_file.filename:
        filename = secure_filename(f"{current_user.id}_{lesson.id}_{answer_file.filename}")
        answer_file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    
    existing = Assignment.query.filter_by(
        student_id=current_user.id, 
        lesson_id=lesson.id
    ).first()
    
    if existing:
        existing.answer_text = answer_text
        existing.answer_file = filename
        existing.submitted_at = datetime.utcnow()
    else:
        assignment = Assignment(
            student_id=current_user.id,
            lesson_id=lesson.id,
            answer_text=answer_text,
            answer_file=filename
        )
        db.session.add(assignment)
    
    db.session.commit()
    flash('Задание успешно отправлено', 'success')
    return redirect(url_for('group_lesson', group_lesson_id=group_lesson.id))

@app.route('/lesson/<int:lesson_id>/grade/<int:assignment_id>', methods=['POST'])
@login_required
def grade_assignment(lesson_id, assignment_id):
    if current_user.role != 'teacher':
        flash('Доступ запрещен', 'danger')
        return redirect(url_for('index'))
    
    assignment = Assignment.query.get_or_404(assignment_id)
    lesson = assignment.lesson
    course = lesson.course
    
    # Проверяем, что преподаватель имеет доступ к курсу
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cur.execute("""
            SELECT * FROM teacher_course 
            WHERE teacher_id = %s AND course_id = %s
        """, (current_user.id, course.id))
        has_access = cur.fetchone()
        
        if not has_access:
            flash('У вас нет доступа к этому курсу', 'danger')
            return redirect(url_for('index'))
    finally:
        cur.close()
        conn.close()
    
    # Находим GroupLesson для перенаправления
    group_lesson = GroupLesson.query.filter_by(
        lesson_id=lesson.id, 
        group_id=assignment.student.group_id
    ).first()
    
    score = request.form.get('score')
    feedback = request.form.get('feedback')
    
    if score:
        assignment.score = int(score)
    assignment.feedback = feedback
    db.session.commit()
    
    flash('Оценка сохранена', 'success')
    if group_lesson:
        return redirect(url_for('group_lesson', group_lesson_id=group_lesson.id))
    else:
        return redirect(url_for('course', course_id=course.id))

@app.route('/test/<int:lesson_id>/group/<int:group_id>', methods=['GET', 'POST'])
@login_required
def take_test(lesson_id, group_id):
    if current_user.role != 'student':
        flash('Доступ запрещен', 'danger')
        return redirect(url_for('index'))
    
    lesson = Lesson.query.get_or_404(lesson_id)
    group = Group.query.get_or_404(group_id)
    
    if current_user.group_id != group.id:
        flash('У вас нет доступа', 'danger')
        return redirect(url_for('index'))
    
    group_lesson = GroupLesson.query.filter_by(group_id=group.id, lesson_id=lesson.id).first()
    if not group_lesson:
        flash('Этот урок не доступен вашей группе', 'danger')
        return redirect(url_for('index'))
    
    assignment = Assignment.query.filter_by(student_id=current_user.id, lesson_id=lesson.id).first()
    
    if assignment and assignment.test_answers:
        flash('Вы уже прошли этот тест', 'info')
        return redirect(url_for('group_lesson', group_lesson_id=group_lesson.id))
    
    if request.method == 'POST':
        if not assignment:
            assignment = Assignment(student_id=current_user.id, lesson_id=lesson.id)
            db.session.add(assignment)
            db.session.flush()
        
        questions = lesson.questions
        score = 0
        
        for question in questions:
            answer = request.form.get(f'question_{question.id}')
            if answer:
                is_correct = (answer == question.correct_answer)
                if is_correct:
                    score += 1
                
                test_answer = TestAnswer(
                    assignment_id=assignment.id,
                    question_id=question.id,
                    answer=answer,
                    is_correct=is_correct
                )
                db.session.add(test_answer)
        
        total = len(questions)
        assignment.score = score
        assignment.feedback = f"Результат: {score} из {total} правильных ответов"
        db.session.commit()
        
        flash(f'Тест завершен! Результат: {score} из {total}', 'success')
        return redirect(url_for('group_lesson', group_lesson_id=group_lesson.id))
    
    questions = lesson.questions
    return render_template('take_test.html', lesson=lesson, questions=questions, group=group, group_lesson_id=group_lesson.id)

@app.route('/uploads/<filename>')
@login_required
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/admin')
@login_required
def admin_dashboard():
    if current_user.role != 'admin':
        flash('Доступ запрещен', 'danger')
        return redirect(url_for('index'))
    
    users = User.query.all()
    groups = Group.query.all()
    courses = Course.query.all()
    return render_template('admin_dashboard.html', users=users, groups=groups, courses=courses)

@app.route('/admin/add_user', methods=['GET', 'POST'])
@login_required
def add_user():
    if current_user.role != 'admin':
        flash('Доступ запрещен', 'danger')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        name = request.form.get('name')
        role = request.form.get('role')
        group_id = request.form.get('group_id')
        
        if User.query.filter_by(email=email).first():
            flash('Пользователь с таким email уже существует', 'danger')
            return redirect(url_for('add_user'))
        
        user = User(
            email=email,
            password_hash=generate_password_hash(password),
            name=name,
            role=role,
            group_id=int(group_id) if group_id and group_id != '' else None
        )
        db.session.add(user)
        db.session.commit()
        flash('Пользователь успешно добавлен', 'success')
        return redirect(url_for('admin_dashboard'))
    
    groups = Group.query.all()
    return render_template('add_user.html', groups=groups)

@app.route('/admin/edit_user/<int:user_id>', methods=['GET', 'POST'])
@login_required
def edit_user(user_id):
    if current_user.role != 'admin':
        flash('Доступ запрещен', 'danger')
        return redirect(url_for('index'))
    
    user = User.query.get_or_404(user_id)
    
    if user.id == current_user.id:
        flash('Нельзя редактировать свою учетную запись здесь.', 'warning')
        return redirect(url_for('admin_dashboard'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        role = request.form.get('role')
        group_id = request.form.get('group_id')
        new_password = request.form.get('new_password')
        
        user.name = name
        user.role = role
        user.group_id = int(group_id) if group_id and group_id != '' else None
        
        if new_password and new_password.strip():
            user.password_hash = generate_password_hash(new_password)
            flash('Пароль успешно изменен', 'success')
        
        db.session.commit()
        flash(f'Пользователь "{user.name}" успешно обновлен', 'success')
        return redirect(url_for('admin_dashboard'))
    
    groups = Group.query.all()
    return render_template('edit_user.html', user=user, groups=groups)

@app.route('/admin/add_group', methods=['GET', 'POST'])
@login_required
def add_group():
    if current_user.role != 'admin':
        flash('Доступ запрещен', 'danger')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        group = Group(name=name)
        db.session.add(group)
        db.session.commit()
        flash('Группа успешно создана', 'success')
        return redirect(url_for('admin_dashboard'))
    
    return render_template('add_group.html')

@app.route('/admin/add_course', methods=['GET', 'POST'])
@login_required
def add_course():
    if current_user.role != 'admin':
        flash('Доступ запрещен', 'danger')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        teacher_ids = request.form.getlist('teachers')
        
        course = Course(title=title, description=description)
        db.session.add(course)
        db.session.flush()
        
        for teacher_id in teacher_ids:
            teacher = User.query.get(int(teacher_id))
            if teacher and teacher.role == 'teacher':
                course.teachers.append(teacher)
        
        db.session.commit()
        flash('Курс успешно создан', 'success')
        return redirect(url_for('admin_dashboard'))
    
    teachers = User.query.filter_by(role='teacher').all()
    return render_template('add_course.html', teachers=teachers)

@app.route('/admin/delete_user/<int:user_id>')
@login_required
def delete_user(user_id):
    if current_user.role != 'admin':
        flash('Доступ запрещен', 'danger')
        return redirect(url_for('index'))
    
    user = User.query.get_or_404(user_id)
    if user.role == 'admin':
        flash('Нельзя удалить администратора', 'danger')
    else:
        db.session.delete(user)
        db.session.commit()
        flash('Пользователь удален', 'success')
    
    return redirect(url_for('admin_dashboard'))

if __name__ == '__main__':
    os.makedirs('uploads', exist_ok=True)
    app.run(debug=True, host='0.0.0.0', port=5000)
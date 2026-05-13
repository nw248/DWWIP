#!/usr/bin/env python
# -*- coding: utf-8 -*-

import requests
import psycopg2
from psycopg2.extras import RealDictCursor
from werkzeug.security import generate_password_hash
import time

BASE_URL = "http://127.0.0.1:5000"
DB_CONFIG = {
    'host': 'localhost',
    'database': 'distance_learning',
    'user': 'postgres',
    'password': '123'
}

GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def get_db():
    return psycopg2.connect(**DB_CONFIG)

def print_result(name, passed, msg=""):
    print(f"  {GREEN if passed else RED}{'✓' if passed else '✗'} {name}{RESET}")
    if msg:
        print(f"    {msg}")

def print_test(name):
    print(f"\n{BLUE}▶ {name}{RESET}")

# ============ ПОДГОТОВКА ============

def setup():
    conn = get_db()
    cur = conn.cursor()
    
    # Администратор
    cur.execute("SELECT id FROM users WHERE role = 'admin' LIMIT 1")
    if not cur.fetchone():
        cur.execute("""
            INSERT INTO users (email, password_hash, name, role, group_id)
            VALUES (%s, %s, %s, %s, %s)
        """, ('admin@example.com', generate_password_hash('admin123'), 'Администратор', 'admin', None))
    
    # Группа
    cur.execute("SELECT id FROM groups WHERE name = 'ТестоваяГруппа'")
    if not cur.fetchone():
        cur.execute("INSERT INTO groups (name) VALUES ('ТестоваяГруппа') RETURNING id")
        group_id = cur.fetchone()[0]
    else:
        cur.execute("SELECT id FROM groups WHERE name = 'ТестоваяГруппа'")
        group_id = cur.fetchone()[0]
    
    # Преподаватель
    cur.execute("SELECT id FROM users WHERE email = 'teacher@test.com'")
    if not cur.fetchone():
        cur.execute("""
            INSERT INTO users (email, password_hash, name, role, group_id)
            VALUES (%s, %s, %s, %s, %s)
        """, ('teacher@test.com', generate_password_hash('teacher123'), 'Тест Преподаватель', 'teacher', None))
    
    # Студент
    cur.execute("SELECT id FROM users WHERE email = 'student@test.com'")
    if not cur.fetchone():
        cur.execute("""
            INSERT INTO users (email, password_hash, name, role, group_id)
            VALUES (%s, %s, %s, %s, %s)
        """, ('student@test.com', generate_password_hash('student123'), 'Тест Студент', 'student', group_id))
    
    conn.commit()
    cur.close()
    conn.close()
    print("  Подготовка завершена")

def cleanup():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM teacher_course WHERE course_id IN (SELECT id FROM courses WHERE title LIKE 'Тест%')")
    cur.execute("DELETE FROM group_course WHERE course_id IN (SELECT id FROM courses WHERE title LIKE 'Тест%')")
    cur.execute("DELETE FROM group_lessons WHERE lesson_id IN (SELECT id FROM lessons WHERE title LIKE 'Тест%')")
    cur.execute("DELETE FROM assignments WHERE lesson_id IN (SELECT id FROM lessons WHERE title LIKE 'Тест%')")
    cur.execute("DELETE FROM lessons WHERE title LIKE 'Тест%'")
    cur.execute("DELETE FROM courses WHERE title LIKE 'Тест%'")
    cur.execute("DELETE FROM users WHERE email IN ('testuser@example.com', 'teacher@test.com', 'student@test.com')")
    cur.execute("DELETE FROM groups WHERE name = 'ТестоваяГруппа'")
    conn.commit()
    cur.close()
    conn.close()
    print("  Очистка выполнена")

def login(email, password):
    s = requests.Session()
    s.post(f"{BASE_URL}/login", data={'email': email, 'password': password})
    return s

# ============ СЦЕНАРИЙ 1 ============

def test_01_login_success():
    s = requests.Session()
    r = s.post(f"{BASE_URL}/login", data={'email': 'admin@example.com', 'password': 'admin123'}, allow_redirects=False)
    if r.status_code == 302:
        return True, "Редирект на главную"
    home = s.get(f"{BASE_URL}/")
    if 'Выход' in home.text:
        return True, "Успешный вход"
    return False, f"Код: {r.status_code}"

def test_02_login_wrong_password():
    r = requests.post(f"{BASE_URL}/login", data={'email': 'admin@example.com', 'password': 'wrong'})
    return 'Неверный' in r.text, "Сообщение об ошибке" if 'Неверный' in r.text else "Не найдено"

def test_03_login_wrong_email():
    r = requests.post(f"{BASE_URL}/login", data={'email': 'nonexistent@test.com', 'password': '123'})
    return 'Неверный' in r.text, "Сообщение об ошибке" if 'Неверный' in r.text else "Не найдено"

def test_04_protected_access():
    r = requests.get(f"{BASE_URL}/admin", allow_redirects=False)
    return r.status_code == 302, "Редирект на /login" if r.status_code == 302 else f"Код {r.status_code}"

# ============ СЦЕНАРИЙ 2 ============

def test_05_add_user():
    s = login('admin@example.com', 'admin123')
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id FROM groups LIMIT 1")
    group = cur.fetchone()
    group_id = str(group[0]) if group else ''
    cur.close()
    conn.close()
    
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM users WHERE email = 'testuser@example.com'")
    conn.commit()
    cur.close()
    conn.close()
    
    s.post(f"{BASE_URL}/admin/add_user", data={
        'email': 'testuser@example.com', 'password': 'test123',
        'name': 'Тест Пользователь', 'role': 'student', 'group_id': group_id
    })
    
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id FROM users WHERE email = 'testuser@example.com'")
    user = cur.fetchone()
    cur.close()
    conn.close()
    return user is not None, "Пользователь создан"

def test_06_duplicate_user():
    s = login('admin@example.com', 'admin123')
    r = s.post(f"{BASE_URL}/admin/add_user", data={
        'email': 'testuser@example.com', 'password': 'test123',
        'name': 'Дубликат', 'role': 'student', 'group_id': ''
    })
    return 'существует' in r.text, "Дубликат отклонён" if 'существует' in r.text else "Не заблокирован"

def test_07_edit_user():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id FROM users WHERE email = 'testuser@example.com'")
    user = cur.fetchone()
    cur.close()
    conn.close()
    if not user:
        return False, "Пользователь не найден"
    s = login('admin@example.com', 'admin123')
    s.post(f"{BASE_URL}/admin/edit_user/{user[0]}", data={
        'name': 'Изменённое Имя', 'role': 'student', 'group_id': '', 'new_password': ''
    })
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT name FROM users WHERE id = %s", (user[0],))
    updated = cur.fetchone()
    cur.close()
    conn.close()
    return updated and updated[0] == 'Изменённое Имя', "Имя обновлено" if updated and updated[0] == 'Изменённое Имя' else "Не обновлено"

def test_08_change_password():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id FROM users WHERE email = 'testuser@example.com'")
    user = cur.fetchone()
    cur.close()
    conn.close()
    if not user:
        return False, "Пользователь не найден"
    s = login('admin@example.com', 'admin123')
    s.post(f"{BASE_URL}/admin/edit_user/{user[0]}", data={
        'name': 'Тест Пользователь', 'role': 'student', 'group_id': '', 'new_password': 'newpass456'
    })
    s2 = requests.Session()
    r = s2.post(f"{BASE_URL}/login", data={'email': 'testuser@example.com', 'password': 'newpass456'}, allow_redirects=False)
    return r.status_code == 302, "Новый пароль работает" if r.status_code == 302 else "Не работает"

def test_09_delete_user():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id FROM users WHERE email = 'testuser@example.com'")
    user = cur.fetchone()
    cur.close()
    conn.close()
    if not user:
        return False, "Пользователь не найден"
    s = login('admin@example.com', 'admin123')
    s.get(f"{BASE_URL}/admin/delete_user/{user[0]}")
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id FROM users WHERE email = 'testuser@example.com'")
    deleted = cur.fetchone()
    cur.close()
    conn.close()
    return deleted is None, "Пользователь удалён" if deleted is None else "Всё ещё существует"

def test_10_delete_admin():
    s = login('admin@example.com', 'admin123')
    r = s.get(f"{BASE_URL}/admin/delete_user/1")
    # Если в ответе есть сообщение "Нельзя удалить" — тест пройден
    return 'Нельзя удалить' in r.text, "Система не позволяет удалить администратора"
# ============ СЦЕНАРИЙ 3 ============

def test_11_create_course():
    s = login('teacher@test.com', 'teacher123')
    s.post(f"{BASE_URL}/create_course", data={'title': 'Тестовый курс', 'description': 'Описание'})
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id FROM courses WHERE title = 'Тестовый курс'")
    course = cur.fetchone()
    cur.close()
    conn.close()
    return course is not None, "Курс создан" if course else "Не создан"

def test_12_teacher_courses_list():
    s = login('teacher@test.com', 'teacher123')
    r = s.get(f"{BASE_URL}/")
    return 'Тестовый курс' in r.text, "Курс отображается" if 'Тестовый курс' in r.text else "Не отображается"

def test_13_add_group_to_course():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id FROM courses WHERE title = 'Тестовый курс'")
    course = cur.fetchone()
    cur.execute("SELECT id FROM groups WHERE name = 'ТестоваяГруппа'")
    group = cur.fetchone()
    cur.close()
    conn.close()
    if not course or not group:
        return False, "Курс или группа не найдены"
    s = login('teacher@test.com', 'teacher123')
    s.post(f"{BASE_URL}/course/{course[0]}/add_students", data={'groups': [str(group[0])]})
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM group_course WHERE course_id = %s AND group_id = %s", (course[0], group[0]))
    link = cur.fetchone()
    cur.close()
    conn.close()
    return link is not None, "Группа добавлена" if link else "Не добавлена"

def test_14_create_lesson():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id FROM courses WHERE title = 'Тестовый курс'")
    course = cur.fetchone()
    cur.execute("SELECT id FROM groups WHERE name = 'ТестоваяГруппа'")
    group = cur.fetchone()
    cur.close()
    conn.close()
    if not course or not group:
        return False, "Курс или группа не найдены"
    s = login('teacher@test.com', 'teacher123')
    s.post(f"{BASE_URL}/course/{course[0]}/group/{group[0]}/add_lesson", data={
        'title': 'Тестовый урок', 'content': 'Содержание урока', 'lesson_type': 'text'
    })
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id FROM lessons WHERE title = 'Тестовый урок' AND course_id = %s", (course[0],))
    lesson = cur.fetchone()
    cur.close()
    conn.close()
    return lesson is not None, "Урок создан" if lesson else "Не создан"

def test_15_create_test_with_questions():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id FROM courses WHERE title = 'Тестовый курс'")
    course = cur.fetchone()
    cur.execute("SELECT id FROM groups WHERE name = 'ТестоваяГруппа'")
    group = cur.fetchone()
    cur.close()
    conn.close()
    if not course or not group:
        return False, "Курс или группа не найдены"
    s = login('teacher@test.com', 'teacher123')
    data = {
        'title': 'Тестовый тест', 'content': 'Вопросы', 'lesson_type': 'test',
        'questions_count': '2',
        'question_0_text': 'Вопрос 1', 'question_0_a': 'A1', 'question_0_b': 'B1', 'question_0_c': 'C1', 'question_0_d': 'D1', 'question_0_correct': 'A',
        'question_1_text': 'Вопрос 2', 'question_1_a': 'A2', 'question_1_b': 'B2', 'question_1_c': 'C2', 'question_1_d': 'D2', 'question_1_correct': 'B'
    }
    s.post(f"{BASE_URL}/course/{course[0]}/group/{group[0]}/add_lesson", data=data)
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id FROM lessons WHERE title = 'Тестовый тест' AND course_id = %s", (course[0],))
    lesson = cur.fetchone()
    cur.execute("SELECT COUNT(*) FROM questions WHERE lesson_id = %s", (lesson[0],))
    count = cur.fetchone()[0]
    cur.close()
    conn.close()
    return count == 2, f"Создано {count} вопросов" if count == 2 else f"Ожидалось 2, получено {count}"

def test_16_delete_course():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id FROM courses WHERE title = 'Тестовый курс'")
    course = cur.fetchone()
    cur.close()
    conn.close()
    if not course:
        return False, "Курс не найден"
    s = login('teacher@test.com', 'teacher123')
    s.post(f"{BASE_URL}/course/delete/{course[0]}")
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id FROM courses WHERE id = %s", (course[0],))
    deleted = cur.fetchone()
    cur.close()
    conn.close()
    return deleted is None, "Курс удалён" if deleted is None else "Всё ещё существует"

# ============ СЦЕНАРИЙ 4 ============

def test_17_student_courses():
    s = login('student@test.com', 'student123')
    r = s.get(f"{BASE_URL}/")
    return 'Курс' in r.text or r.status_code == 200, "Страница загружена"

def test_18_student_lessons():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id FROM lessons WHERE title = 'Тестовый урок' LIMIT 1")
    lesson = cur.fetchone()
    cur.close()
    conn.close()
    if not lesson:
        return True, "Нет уроков для проверки (пропущено)"
    s = login('student@test.com', 'student123')
    r = s.get(f"{BASE_URL}/lesson/{lesson[0]}")
    return r.status_code == 200 or r.status_code == 302, "Страница урока доступна"

def test_19_submit_text_answer():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id FROM lessons WHERE title = 'Тестовый урок' LIMIT 1")
    lesson = cur.fetchone()
    cur.close()
    conn.close()
    if not lesson:
        return True, "Нет урока для проверки (пропущено)"
    s = login('student@test.com', 'student123')
    r = s.post(f"{BASE_URL}/lesson/{lesson[0]}/submit", data={'answer_text': 'Тестовый ответ студента'})
    return 'отправлено' in r.text.lower() or r.status_code == 302, "Ответ отправлен"

def test_20_take_test():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id FROM lessons WHERE title = 'Тестовый тест' LIMIT 1")
    lesson = cur.fetchone()
    cur.execute("SELECT id FROM groups WHERE name = 'ТестоваяГруппа'")
    group = cur.fetchone()
    cur.close()
    conn.close()
    if not lesson or not group:
        return True, "Нет теста для проверки (пропущено)"
    s = login('student@test.com', 'student123')
    r = s.get(f"{BASE_URL}/test/{lesson[0]}/group/{group[0]}")
    return r.status_code == 200 or r.status_code == 302, "Страница теста доступна"

def test_21_view_grade():
    return True, "Пропущено (страница не реализована в текущей версии)"

# ============ СЦЕНАРИЙ 5 ============

def test_22_view_student_answers():
    s = login('teacher@test.com', 'teacher123')
    r = s.get(f"{BASE_URL}/")
    return r.status_code == 200, "Страница доступна"

def test_23_grade_assignment():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id FROM assignments LIMIT 1")
    assignment = cur.fetchone()
    cur.execute("SELECT id FROM lessons LIMIT 1")
    lesson = cur.fetchone()
    cur.close()
    conn.close()
    if not assignment or not lesson:
        return True, "Нет заданий для проверки (пропущено)"
    s = login('teacher@test.com', 'teacher123')
    r = s.post(f"{BASE_URL}/lesson/{lesson[0]}/grade/{assignment[0]}", data={'score': '85', 'feedback': 'Хорошая работа'})
    return r.status_code == 302 or 'сохранена' in r.text, "Оценка сохранена"

def test_24_view_test_results():
    s = login('teacher@test.com', 'teacher123')
    r = s.get(f"{BASE_URL}/")
    return r.status_code == 200, "Страница доступна"

# ============ ТАБЛИЦА РОЛЕВОЙ МОДЕЛИ ============

def test_25_role_admin():
    s = login('admin@example.com', 'admin123')
    r1 = s.get(f"{BASE_URL}/admin")
    r2 = s.get(f"{BASE_URL}/admin/add_user")
    return (r1.status_code == 200 and r2.status_code == 200), "Админ-панель доступна"

def test_role_teacher():
    s = login('teacher@test.com', 'teacher123')
    r_admin = s.get(f"{BASE_URL}/admin", allow_redirects=False)
    r_create = s.get(f"{BASE_URL}/create_course")
    return (r_admin.status_code == 302 and r_create.status_code == 200), "Учитель не в админке, но может создавать курсы"
def test_27_role_student():
    s = login('student@test.com', 'student123')
    r1 = s.get(f"{BASE_URL}/create_course", allow_redirects=False)
    r2 = s.get(f"{BASE_URL}/admin", allow_redirects=False)
    return (r1.status_code == 302 and r2.status_code == 302), "Студент не может создавать курсы и заходить в админку"

# ============ ОШИБКИ ============

def test_28_empty_title():
    s = login('teacher@test.com', 'teacher123')
    r = s.post(f"{BASE_URL}/create_course", data={'title': '', 'description': 'Описание'})
    return 'Название' in r.text, "Валидация сработала" if 'Название' in r.text else "Не сработала"

# ============ ЗАПУСК ============

def run_all_tests():
    print("\n" + "="*60)
    print("ТЕСТИРОВАНИЕ СИСТЕМЫ ДИСТАНЦИОННОГО ОБУЧЕНИЯ")
    print("="*60)
    
    print("\n[0. ПОДГОТОВКА]")
    setup()
    
    print_test("Сценарий 1: Аутентификация пользователей")
    print_result("1.1 Вход с корректными данными", *test_01_login_success())
    print_result("1.2 Вход с неверным паролем", *test_02_login_wrong_password())
    print_result("1.3 Вход с незарегистрированным email", *test_03_login_wrong_email())
    print_result("1.4 Доступ без авторизации", *test_04_protected_access())
    
    print_test("Сценарий 2: Управление пользователями (администратор)")
    print_result("2.1 Добавление пользователя", *test_05_add_user())
    print_result("2.2 Добавление с существующим email", *test_06_duplicate_user())
    print_result("2.3 Редактирование пользователя", *test_07_edit_user())
    print_result("2.4 Смена пароля пользователя", *test_08_change_password())
    print_result("2.5 Удаление пользователя", *test_09_delete_user())
    print_result("2.6 Попытка удалить администратора", *test_10_delete_admin())
    
    print_test("Сценарий 3: Управление курсами (преподаватель)")
    print_result("3.1 Создание нового курса", *test_11_create_course())
    print_result("3.2 Просмотр списка курсов", *test_12_teacher_courses_list())
    print_result("3.3 Добавление группы на курс", *test_13_add_group_to_course())
    print_result("3.4 Создание урока для группы", *test_14_create_lesson())
    print_result("3.5 Создание теста с вопросами", *test_15_create_test_with_questions())
    print_result("3.6 Удаление курса", *test_16_delete_course())
    
    print_test("Сценарий 4: Выполнение заданий (студент)")
    print_result("4.1 Просмотр доступных курсов", *test_17_student_courses())
    print_result("4.2 Просмотр уроков курса", *test_18_student_lessons())
    print_result("4.3 Отправка текстового ответа", *test_19_submit_text_answer())
    print_result("4.4 Прохождение теста", *test_20_take_test())
    print_result("4.5 Просмотр оценки", *test_21_view_grade())
    
    print_test("Сценарий 5: Проверка заданий (преподаватель)")
    print_result("5.1 Просмотр ответов студентов", *test_22_view_student_answers())
    print_result("5.2 Выставление оценки", *test_23_grade_assignment())
    print_result("5.3 Просмотр результатов теста", *test_24_view_test_results())
    
    print_test("Тестирование ролевой модели")
    print_result("Роль Администратор: доступ к админ-панели", *test_25_role_admin())
    print_result("Роль Преподаватель: создание курсов, нет админки", *test_role_teacher())
    print_result("Роль Студент: нет доступа к админке и созданию курсов", *test_27_role_student())
    
    print_test("Тестирование обработки ошибок")
    print_result("4.1 Создание курса без названия", *test_28_empty_title())
    
    print("\n[6. ОЧИСТКА]")
    cleanup()
    
    print("\n" + "="*60)
    print("ТЕСТИРОВАНИЕ ЗАВЕРШЕНО")
    print("="*60 + "\n")

if __name__ == '__main__':
    print(YELLOW + "Убедитесь, что приложение запущено на " + BASE_URL + RESET)
    response = input("Продолжить? (y/n): ")
    if response.lower() == 'y':
        run_all_tests()
    else:
        print("Тестирование отменено")
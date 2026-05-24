#!/usr/bin/env python
# -*- coding: utf-8 -*-

import requests
import psycopg2
from psycopg2.extras import RealDictCursor
from werkzeug.security import generate_password_hash

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

def setup():
    conn = get_db()
    cur = conn.cursor()
    
    cur.execute("SELECT id FROM users WHERE email = 'admin@test.com'")
    if not cur.fetchone():
        cur.execute("""
            INSERT INTO users (email, password_hash, name, role, group_id)
            VALUES (%s, %s, %s, %s, %s)
        """, ('admin@test.com', generate_password_hash('admin123'), 'Тест Админ', 'admin', None))
    
    cur.execute("SELECT id FROM users WHERE email = 'teacher@test.com'")
    if not cur.fetchone():
        cur.execute("""
            INSERT INTO users (email, password_hash, name, role, group_id)
            VALUES (%s, %s, %s, %s, %s)
        """, ('teacher@test.com', generate_password_hash('teacher123'), 'Тест Преподаватель', 'teacher', None))
    
    cur.execute("SELECT id FROM groups WHERE name = 'ТестоваяГруппа'")
    if not cur.fetchone():
        cur.execute("INSERT INTO groups (name) VALUES ('ТестоваяГруппа')")
    
    conn.commit()
    cur.close()
    conn.close()
    print("  Подготовка завершена")

def cleanup():
    conn = get_db()
    cur = conn.cursor()
    try:
        # 1. Удаляем связи преподавателей с курсами
        cur.execute("DELETE FROM teacher_course WHERE teacher_id IN (SELECT id FROM users WHERE email LIKE '%@test.com')")
        
        # 2. Удаляем связи групп с курсами
        cur.execute("DELETE FROM group_course WHERE group_id IN (SELECT id FROM groups WHERE name LIKE '%Тест%' OR name LIKE '%Новая%')")
        
        # 3. Удаляем связи групп с уроками
        cur.execute("DELETE FROM group_lessons WHERE group_id IN (SELECT id FROM groups WHERE name LIKE '%Тест%' OR name LIKE '%Новая%')")
        
        # 4. Удаляем ответы на тесты
        cur.execute("DELETE FROM test_answers WHERE assignment_id IN (SELECT id FROM assignments WHERE lesson_id IN (SELECT id FROM lessons WHERE title LIKE 'Тест%'))")
        
        # 5. Удаляем задания
        cur.execute("DELETE FROM assignments WHERE lesson_id IN (SELECT id FROM lessons WHERE title LIKE 'Тест%')")
        
        # 6. Удаляем вопросы тестов
        cur.execute("DELETE FROM questions WHERE lesson_id IN (SELECT id FROM lessons WHERE title LIKE 'Тест%')")
        
        # 7. Удаляем уроки
        cur.execute("DELETE FROM lessons WHERE title LIKE 'Тест%' OR course_id IN (SELECT id FROM courses WHERE title LIKE 'Тест%')")
        
        # 8. Удаляем курсы
        cur.execute("DELETE FROM courses WHERE title LIKE 'Тест%'")
        
        # 9. Удаляем тестовых пользователей (кроме админа)
        cur.execute("DELETE FROM users WHERE email LIKE '%@test.com' AND role != 'admin'")
        
        # 10. Удаляем тестовые группы
        cur.execute("DELETE FROM groups WHERE name LIKE '%Тест%' OR name LIKE '%Новая%'")
        
        conn.commit()
    except Exception as e:
        print(f"Ошибка очистки: {e}")
        conn.rollback()
    finally:
        cur.close()
        conn.close()
    print("  Очистка выполнена")

def login(email, password):
    s = requests.Session()
    r = s.post(f"{BASE_URL}/api/login", json={'email': email, 'password': password})
    if r.status_code == 200 and r.json().get('success'):
        return s, r.json()['user']
    return None, None

def test_01_login_success():
    s, user = login('admin@test.com', 'admin123')
    if s and user:
        return True, f"Вошёл как {user['name']}"
    return False, "Ошибка входа"

def test_02_login_wrong_password():
    s, _ = login('admin@test.com', 'wrong')
    return s is None, "Доступ запрещён"

def test_03_login_wrong_email():
    s, _ = login('nonexistent@test.com', '123')
    return s is None, "Доступ запрещён"

def test_04_get_courses():
    s, _ = login('teacher@test.com', 'teacher123')
    r = s.get(f"{BASE_URL}/api/courses")
    if r.status_code == 200:
        return True, f"Загружено {len(r.json())} курсов"
    return False, f"Код {r.status_code}"

def test_05_create_course():
    s, _ = login('teacher@test.com', 'teacher123')
    r = s.post(f"{BASE_URL}/api/courses", json={'title': 'Тестовый курс', 'description': 'Описание'})
    if r.status_code == 200 and r.json().get('success'):
        return True, f"Курс создан, id={r.json().get('course_id')}"
    return False, "Ошибка создания"

def test_06_get_groups():
    s, _ = login('admin@test.com', 'admin123')
    r = s.get(f"{BASE_URL}/api/groups")
    if r.status_code == 200:
        return True, f"Загружено {len(r.json())} групп"
    return False, f"Код {r.status_code}"

def test_07_add_group():
    s, _ = login('admin@test.com', 'admin123')
    r = s.post(f"{BASE_URL}/api/groups", json={'name': 'НоваяГруппа'})
    if r.status_code == 200 and r.json().get('success'):
        return True, "Группа создана"
    return False, "Ошибка создания"

def test_08_get_users():
    s, _ = login('admin@test.com', 'admin123')
    r = s.get(f"{BASE_URL}/api/users")
    if r.status_code == 200:
        return True, f"Загружено {len(r.json())} пользователей"
    return False, f"Код {r.status_code}"

def test_09_add_user():
    s, _ = login('admin@test.com', 'admin123')
    r = s.post(f"{BASE_URL}/api/users", json={
        'email': 'newuser@test.com',
        'password': 'Test123!',
        'name': 'Новый Пользователь',
        'role': 'student',
        'group_id': None
    })
    if r.status_code == 200 and r.json().get('success'):
        return True, "Пользователь создан"
    return False, "Ошибка создания"

def test_10_update_user():
    s, _ = login('admin@test.com', 'admin123')
    r = s.get(f"{BASE_URL}/api/users")
    users = r.json()
    user_id = None
    for u in users:
        if u['email'] == 'newuser@test.com':
            user_id = u['id']
            break
    if not user_id:
        return False, "Пользователь не найден"
    
    r = s.put(f"{BASE_URL}/api/users/{user_id}", json={
        'email': 'updated@test.com',
        'new_password': 'NewPass123!'
    })
    if r.status_code == 200:
        return True, "Пользователь обновлён"
    return False, "Ошибка обновления"

def test_11_delete_user():
    s, _ = login('admin@test.com', 'admin123')
    r = s.get(f"{BASE_URL}/api/users")
    users = r.json()
    user_id = None
    for u in users:
        if u['email'] == 'updated@test.com':
            user_id = u['id']
            break
    if not user_id:
        return False, "Пользователь не найден"
    
    r = s.delete(f"{BASE_URL}/api/users/{user_id}")
    if r.status_code == 200:
        return True, "Пользователь удалён"
    return False, "Ошибка удаления"

def test_12_admin_courses():
    s, _ = login('admin@test.com', 'admin123')
    r = s.get(f"{BASE_URL}/api/admin/courses")
    if r.status_code == 200:
        return True, f"Загружено {len(r.json())} курсов"
    return False, f"Код {r.status_code}"

def test_13_logout():
    s, _ = login('admin@test.com', 'admin123')
    r = s.post(f"{BASE_URL}/api/logout")
    if r.status_code == 200:
        return True, "Выход выполнен"
    return False, "Ошибка выхода"

def run_all_tests():
    print("\n" + "="*60)
    print("ТЕСТИРОВАНИЕ API")
    print("="*60)
    
    print("\n[0. ПОДГОТОВКА]")
    setup()
    
    print_test("Сценарий 1: Аутентификация")
    print_result("1.1 Вход с корректными данными", *test_01_login_success())
    print_result("1.2 Вход с неверным паролем", *test_02_login_wrong_password())
    print_result("1.3 Вход с незарегистрированным email", *test_03_login_wrong_email())
    print_result("1.4 Выход из системы", *test_13_logout())
    
    print_test("Сценарий 2: Курсы (преподаватель)")
    print_result("2.1 Просмотр курсов", *test_04_get_courses())
    print_result("2.2 Создание курса", *test_05_create_course())
    
    print_test("Сценарий 3: Группы (администратор)")
    print_result("3.1 Просмотр групп", *test_06_get_groups())
    print_result("3.2 Создание группы", *test_07_add_group())
    
    print_test("Сценарий 4: Пользователи (администратор)")
    print_result("4.1 Просмотр пользователей", *test_08_get_users())
    print_result("4.2 Добавление пользователя", *test_09_add_user())
    print_result("4.3 Редактирование пользователя", *test_10_update_user())
    print_result("4.4 Удаление пользователя", *test_11_delete_user())
    
    print_test("Сценарий 5: Админ-панель")
    print_result("5.1 Просмотр всех курсов", *test_12_admin_courses())
    
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
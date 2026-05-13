import pytest
import requests
import psycopg2

BASE_URL = "http://127.0.0.1:5000"
DB_CONFIG = {
    'host': 'localhost',
    'database': 'distance_learning',
    'user': 'postgres',
    'password': '123'
}

@pytest.fixture
def db_connection():
    conn = psycopg2.connect(**DB_CONFIG)
    yield conn
    conn.close()

@pytest.fixture
def admin_session():
    session = requests.Session()
    session.post(f"{BASE_URL}/login", data={'email': 'admin@example.com', 'password': 'admin123'})
    return session

def test_login_success():
    r = requests.post(f"{BASE_URL}/login", data={'email': 'admin@example.com', 'password': 'admin123'})
    assert r.status_code == 200 or r.status_code == 302

def test_login_wrong_password():
    r = requests.post(f"{BASE_URL}/login", data={'email': 'admin@example.com', 'password': 'wrong'})
    assert 'Неверный' in r.text

def test_protected_page():
    r = requests.get(f"{BASE_URL}/admin", allow_redirects=False)
    assert r.status_code == 302

def test_add_user(db_connection, admin_session):
    cur = db_connection.cursor()
    cur.execute("DELETE FROM users WHERE email = 'pytest@example.com'")
    db_connection.commit()
    
    admin_session.post(f"{BASE_URL}/admin/add_user", data={
        'email': 'pytest@example.com',
        'password': 'pass123',
        'name': 'PyTest User',
        'role': 'student',
        'group_id': ''
    })
    
    cur.execute("SELECT id FROM users WHERE email = 'pytest@example.com'")
    user = cur.fetchone()
    assert user is not None

def test_delete_user(db_connection, admin_session):
    cur = db_connection.cursor()
    cur.execute("SELECT id FROM users WHERE email = 'pytest@example.com'")
    user = cur.fetchone()
    
    if user:
        admin_session.get(f"{BASE_URL}/admin/delete_user/{user[0]}")
        cur.execute("SELECT id FROM users WHERE email = 'pytest@example.com'")
        assert cur.fetchone() is None

def test_create_course(db_connection):
    session = requests.Session()
    session.post(f"{BASE_URL}/login", data={'email': 'test_teacher@example.com', 'password': 'teacher123'})
    session.post(f"{BASE_URL}/create_course", data={'title': 'PyTest Course', 'description': 'Test'})
    
    cur = db_connection.cursor()
    cur.execute("SELECT id FROM courses WHERE title = 'PyTest Course'")
    course = cur.fetchone()
    assert course is not None

def test_courses_table_exists(db_connection):
    cur = db_connection.cursor()
    cur.execute("""
        SELECT table_name FROM information_schema.tables 
        WHERE table_name = 'courses'
    """)
    assert cur.fetchone() is not None
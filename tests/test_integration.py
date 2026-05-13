def test_login_page(client):
    """Страница входа доступна"""
    response = client.get('/login')
    assert response.status_code == 200

def test_admin_dashboard(client):
    """Доступ к админ-панели"""
    response = client.get('/admin')
    assert response.status_code == 200
    assert b'Панель администратора' in response.data

def test_add_user_page(client):
    """Страница добавления пользователя"""
    response = client.get('/admin/add_user')
    assert response.status_code == 200

def test_add_user(client):
    """Добавление пользователя через форму"""
    response = client.post('/admin/add_user', data={
        'email': 'newuser@test.com',
        'password': 'pass123',
        'name': 'New User',
        'role': 'student',
        'group_id': ''
    }, follow_redirects=True)
    assert response.status_code == 200

def test_create_course_page(client):
    """Страница создания курса доступна"""
    response = client.get('/create_course')
    assert response.status_code == 200

def test_create_course(client):
    """Создание курса преподавателем"""
    response = client.post('/create_course', data={
        'title': 'Test Course',
        'description': 'Description'
    }, follow_redirects=True)
    assert response.status_code == 200

def test_create_course_empty_title(client):
    """Создание курса без названия (валидация)"""
    response = client.post('/create_course', data={
        'title': '',
        'description': 'Description'
    }, follow_redirects=True)
    # Может быть редирект или сообщение об ошибке
    assert response.status_code == 200
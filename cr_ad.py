from werkzeug.security import generate_password_hash
import psycopg2

# Конфигурация базы данных
DB_CONFIG = {
    'host': 'localhost',
    'database': 'distance_learning',
    'user': 'postgres',
    'password': '123'
}

# Генерируем правильный хеш пароля
password = 'admin123'
password_hash = generate_password_hash(password)

print(f"Пароль: {password}")
print(f"Хеш: {password_hash}")
print("-" * 50)

# Подключаемся к базе данных
conn = psycopg2.connect(**DB_CONFIG)
cur = conn.cursor()

try:
    # Удаляем старого админа если есть
    cur.execute("DELETE FROM users WHERE email = 'admin@example.com'")
    
    # Добавляем нового администратора с правильным хешем
    cur.execute("""
        INSERT INTO users (email, password_hash, name, role, group_id)
        VALUES (%s, %s, %s, %s, %s)
    """, ('admin@example.com', password_hash, 'Администратор', 'admin', None))
    
    conn.commit()
    print("Администратор успешно создан!")
    print("Email: admin@example.com")
    print("Пароль: admin123")
    
    # Проверяем, что добавилось
    cur.execute("SELECT id, email, name, role FROM users WHERE email = 'admin@example.com'")
    user = cur.fetchone()
    print(f"Проверка: {user}")
    
except Exception as e:
    print(f"Ошибка: {e}")
    conn.rollback()
finally:
    cur.close()
    conn.close()
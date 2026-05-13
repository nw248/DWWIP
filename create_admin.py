#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Скрипт для создания администратора в системе дистанционного обучения
Запуск: python create_admin.py
"""

import psycopg2
from werkzeug.security import generate_password_hash

# Конфигурация базы данных PostgreSQL
DB_CONFIG = {
    'host': 'localhost',
    'database': 'distance_learning',
    'user': 'postgres',
    'password': '123'
}

def get_db_connection():
    """Подключение к базе данных"""
    return psycopg2.connect(**DB_CONFIG)

def create_admin():
    """Создание администратора с правильным хешированным паролем"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        # Проверяем, существует ли уже администратор
        cur.execute("SELECT id, email FROM users WHERE role = 'admin'")
        existing_admin = cur.fetchone()
        
        if existing_admin:
            print(f"Администратор уже существует:")
            print(f"  ID: {existing_admin[0]}")
            print(f"  Email: {existing_admin[1]}")
            print("\nЧтобы создать нового администратора, сначала удалите существующего:")
            print("  DELETE FROM users WHERE role = 'admin';")
            return
        
        # Генерируем правильный хеш пароля
        email = 'admin@example.com'
        password = 'admin123'
        password_hash = generate_password_hash(password)
        
        # Вставляем администратора
        cur.execute("""
            INSERT INTO users (email, password_hash, name, role, group_id)
            VALUES (%s, %s, %s, %s, %s)
        """, (email, password_hash, 'Администратор', 'admin', None))
        
        conn.commit()
        
        print("="*50)
        print("Администратор успешно создан!")
        print(f"  Email: {email}")
        print(f"  Пароль: {password}")
        print("="*50)
        print("\nПароль сохранён в захешированном виде.")
        
    except Exception as e:
        print(f"Ошибка при создании администратора: {e}")
        conn.rollback()
    finally:
        cur.close()
        conn.close()

def delete_all_admins():
    """Удаление всех администраторов (для пересоздания)"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute("SELECT id, email FROM users WHERE role = 'admin'")
        admins = cur.fetchall()
        
        if not admins:
            print("Администраторы не найдены.")
            return
        
        print("Найдены администраторы:")
        for admin in admins:
            print(f"  ID: {admin[0]}, Email: {admin[1]}")
        
        confirm = input("\nУдалить всех администраторов? (y/n): ")
        if confirm.lower() == 'y':
            cur.execute("DELETE FROM users WHERE role = 'admin'")
            conn.commit()
            print(f"Удалено {len(admins)} администратор(ов).")
        else:
            print("Отменено.")
            
    except Exception as e:
        print(f"Ошибка: {e}")
        conn.rollback()
    finally:
        cur.close()
        conn.close()

def reset_admin_password():
    """Сброс пароля существующего администратора"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        # Находим администратора
        cur.execute("SELECT id, email FROM users WHERE role = 'admin' LIMIT 1")
        admin = cur.fetchone()
        
        if not admin:
            print("Администратор не найден. Сначала создайте его.")
            return
        
        print(f"Найден администратор: {admin[1]}")
        new_password = input("Введите новый пароль (по умолчанию admin123): ").strip()
        if not new_password:
            new_password = 'admin123'
        
        password_hash = generate_password_hash(new_password)
        cur.execute("UPDATE users SET password_hash = %s WHERE id = %s", (password_hash, admin[0]))
        conn.commit()
        
        print(f"Пароль для {admin[1]} успешно обновлён!")
        
    except Exception as e:
        print(f"Ошибка: {e}")
        conn.rollback()
    finally:
        cur.close()
        conn.close()

if __name__ == '__main__':
    print("\n" + "="*50)
    print("УПРАВЛЕНИЕ АДМИНИСТРАТОРОМ СИСТЕМЫ")
    print("="*50)
    print("\nВыберите действие:")
    print("  1 - Создать администратора")
    print("  2 - Удалить всех администраторов")
    print("  3 - Сбросить пароль администратора")
    print("  4 - Выйти")
    
    choice = input("\nВаш выбор (1-4): ").strip()
    
    if choice == '1':
        create_admin()
    elif choice == '2':
        delete_all_admins()
    elif choice == '3':
        reset_admin_password()
    else:
        print("До свидания!")
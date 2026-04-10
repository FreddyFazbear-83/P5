import psycopg2
from psycopg2 import pool
from datetime import datetime, timedelta
from typing import Optional, Dict, List

db_pool = None

def init_database() -> bool:
    global db_pool
    try:
        print("Подключение к PostgreSQL...")
        db_pool = pool.SimpleConnectionPool(
            1, 10,
            host="localhost",
            database="dairy_production",
            user="postgres",
            password="redf1ld",
            options='-c client_encoding=UTF8'
        )
        print("База данных подключена!")
        return True
    except Exception as e:
        print(f"Ошибка БД: {e}")
        return False

def get_connection():
    if db_pool is None:
        raise Exception("База данных не инициализирована!")
    return db_pool.getconn()

def release_connection(conn):
    if db_pool is not None:
        db_pool.putconn(conn)

def get_all_roles() -> List:
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT role_id, role_name FROM roles ORDER BY role_id")
        result = cursor.fetchall()
        cursor.close()
        print(f"Загружено ролей: {len(result)}")
        return result if result else []
    except Exception as e:
        print(f"Ошибка получения ролей: {e}")
        return []
    finally:
        release_connection(conn)

def get_user_by_login(login: str) -> Optional[Dict]:
    conn = get_connection()
    try:
        cursor = conn.cursor()
        # Используем lowercase имена колонок (PostgreSQL)
        cursor.execute("""
            SELECT u.userid, u.login, u.password, u.role_id, r.role_name,
                   u.failedattempts, u.islocked, u.lockeduntil
            FROM users u
            JOIN roles r ON u.role_id = r.role_id
            WHERE u.login = %s
        """, (login.strip(),))
        result = cursor.fetchone()
        cursor.close()

        if result:
            print(f"Пользователь найден: {login}")
            print(f"  Role ID: {result[3]}, Role Name: {result[4]}")
            print(f"  Failed: {result[5]}, Locked: {result[6]}")
            return {
                'user_id': result[0],
                'login': result[1],
                'password': result[2],
                'role_id': result[3],
                'role_name': result[4],
                'failed_attempts': result[5] or 0,
                'is_locked': result[6] or False,
                'locked_until': result[7]
            }
        else:
            print(f"Пользователь не найден: {login}")
        return None
    except Exception as e:
        print(f"Ошибка получения пользователя: {e}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        release_connection(conn)

def reset_failed_attempts(user_id: int):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE users
            SET failedattempts = 0, islocked = FALSE, lockeduntil = NULL
            WHERE userid = %s
        """, (user_id,))
        conn.commit()
        cursor.close()
        print(f"✅ Сброшены попытки для пользователя {user_id}")
    except Exception as e:
        print(f"Ошибка сброса: {e}")
        conn.rollback()
    finally:
        release_connection(conn)

def increment_failed_attempts(user_id: int) -> int:
    """Увеличить счётчик попыток на 1 и вернуть новое значение"""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT failedattempts FROM users WHERE userid = %s
        """, (user_id,))
        result = cursor.fetchone()
        current_attempts = (result[0] or 0) + 1

        print(f"Попытка входа {current_attempts} для пользователя {user_id}")

        if current_attempts >= 3:
            lock_until = datetime.now() + timedelta(minutes=15)
            cursor.execute("""
                UPDATE users
                SET failedattempts = %s, islocked = TRUE, lockeduntil = %s
                WHERE userid = %s
            """, (current_attempts, lock_until, user_id))
            print(f"🚫 Пользователь {user_id} заблокирован до {lock_until}")
        else:
            cursor.execute("""
                UPDATE users SET failedattempts = %s WHERE userid = %s
            """, (current_attempts, user_id))

        conn.commit()
        cursor.close()
        return current_attempts
    except Exception as e:
        print(f"Ошибка инкремента: {e}")
        conn.rollback()
        return 0
    finally:
        release_connection(conn)

def verify_password(input_pwd: str, stored_pwd: str) -> bool:
    try:
        import bcrypt
        if bcrypt.checkpw(input_pwd.encode('utf-8'), stored_pwd.encode('utf-8')):
            print("Пароль проверен через bcrypt")
            return True
    except Exception as e:
        print(f"ℹ️ bcrypt не сработал: {e}")
        pass

    if input_pwd == stored_pwd:
        print("Пароль проверен (простое сравнение)")
        return True

    print("Пароль не совпадает")
    return False

def get_all_users() -> List:
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT u.userid, u.login, r.role_name, u.failedattempts, u.islocked
            FROM users u
            JOIN roles r ON u.role_id = r.role_id
            ORDER BY u.userid
        """)
        result = cursor.fetchall()
        cursor.close()
        print(f"Загружено пользователей: {len(result)}")
        return result if result else []
    except Exception as e:
        print(f"Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return []
    finally:
        release_connection(conn)


def create_user(login: str, password: str, role_id: int) -> bool:
    print(f"➕ Создание пользователя: login={login}, role_id={role_id}")

    if get_user_by_login(login):
        print(f"Пользователь {login} уже существует")
        return False

    conn = get_connection()
    try:
        cursor = conn.cursor()

        try:
            import bcrypt
            hashed_password = bcrypt.hashpw(
                password.encode('utf-8'),
                bcrypt.gensalt()
            ).decode('utf-8')
            print("Пароль захеширован bcrypt")
        except:
            hashed_password = password
            print("ℹПароль сохранён как текст")

        cursor.execute("""
            INSERT INTO users (login, password, role_id, failedattempts, islocked)
            VALUES (%s, %s, %s, 0, FALSE)
        """, (login.strip(), hashed_password, role_id))

        conn.commit()
        cursor.close()
        print(f"Пользователь {login} создан успешно!")
        return True
    except Exception as e:
        print(f"Ошибка создания пользователя: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        release_connection(conn)

def update_user(user_id: int, login: str, role_id: int, is_locked: bool) -> bool:
    conn = get_connection()
    try:
        cursor = conn.cursor()
        if not is_locked:
            cursor.execute("""
                UPDATE users
                SET login = COALESCE(NULLIF(%s, ''), login), 
                    role_id = COALESCE(NULLIF(%s, 0), role_id), 
                    islocked = %s,
                    failedattempts = 0,
                    lockeduntil = NULL
                WHERE userid = %s
            """, (login if login else None, role_id if role_id else None, is_locked, user_id))
        else:
            cursor.execute("""
                UPDATE users
                SET login = COALESCE(NULLIF(%s, ''), login), 
                    role_id = COALESCE(NULLIF(%s, 0), role_id), 
                    islocked = %s
                WHERE userid = %s
            """, (login if login else None, role_id if role_id else None, is_locked, user_id))

        conn.commit()
        cursor.close()
        print(f"Пользователь {user_id} обновлён")
        return True
    except Exception as e:
        print(f"Ошибка обновления: {e}")
        conn.rollback()
        return False
    finally:
        release_connection(conn)

def check_login_exists(login: str, exclude_user_id: int = None) -> bool:
    conn = get_connection()
    try:
        cursor = conn.cursor()
        if exclude_user_id:
            cursor.execute("""
                SELECT COUNT(*) FROM users
                WHERE login = %s AND userid != %s
            """, (login.strip(), exclude_user_id))
        else:
            cursor.execute("""
                SELECT COUNT(*) FROM users WHERE login = %s
            """, (login.strip(),))
        result = cursor.fetchone()
        cursor.close()
        exists = result[0] > 0 if result else False
        print(f"Проверка логина {login}: {'существует' if exists else 'не существует'}")
        return exists
    except Exception as e:
        print(f"Ошибка проверки логина: {e}")
        return False
    finally:
        release_connection(conn)

def get_all_customers() -> List:
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT customercode, customername, inn, address, phone,
                   issupplier, isbuyer
            FROM customers
            ORDER BY customercode
        """)
        result = cursor.fetchall()
        cursor.close()
        return result if result else []
    except Exception as e:
        print(f"Ошибка: {e}")
        return []
    finally:
        release_connection(conn)

def get_order_cost_calculation(order_number: str = None) -> List:
    conn = get_connection()
    try:
        cursor = conn.cursor()
        if order_number:
            cursor.execute("""
                SELECT * FROM vw_order_cost_calculation
                WHERE order_number = %s
                ORDER BY product_code
            """, (order_number,))
        else:
            cursor.execute("""
                SELECT * FROM vw_order_cost_calculation
                ORDER BY order_number, product_code
            """)
        result = cursor.fetchall()
        cursor.close()
        return result if result else []
    except Exception as e:
        print(f"Ошибка: {e}")
        return []
    finally:
        release_connection(conn)
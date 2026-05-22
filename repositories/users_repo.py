from database import get_connection

class UserRepository:
    def create_user(self, username, email, password_hash):
        conn = get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)""", (username, email, password_hash,))
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def get_by_email(self, email):
        conn = get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""SELECT id, username, email, password_hash FROM users WHERE email=?""", (email,))
            user = cursor.fetchone()
            return user
        finally:
            conn.close()

    def get_by_id(self, user_id):
        conn = get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""SELECT id, username, email FROM users WHERE id=?""", (user_id,))
            user = cursor.fetchone()
            return user
        finally:
            conn.close()

    def update_password(self, user_id, new_password):
        conn = get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""UPDATE users SET password_hash = ? WHERE id = ?""", (new_password, user_id))
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def get_password_hash(self, user_id):
        conn = get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""SELECT password_hash FROM users WHERE id = ?""", (user_id,))
            result = cursor.fetchone()
            return result["password_hash"] if result else None
        finally:
            conn.close()

    def get_all_users(self):
        conn = get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT id, username, email FROM users")
            return cursor.fetchall()
        finally:
            conn.close()
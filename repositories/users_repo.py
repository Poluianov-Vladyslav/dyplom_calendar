from database import get_connection

class UserRepository:
    def create_user(self, username, email, password_hash):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)""", (username, email, password_hash,))
        conn.commit()
        conn.close()

    def get_by_email(self, email):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""SELECT id, username, email, password_hash FROM users WHERE email=?""", (email,))
        user = cursor.fetchone()
        conn.close()
        return user

    def get_by_id(self, user_id):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""SELECT id, username, email FROM users WHERE id=?""", (user_id,))
        user = cursor.fetchone()
        conn.close()
        return user

    def update_password(self, user_id, new_password):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""UPDATE users SET password_hash = ? WHERE id = ?""", (new_password, user_id))
        conn.commit()
        conn.close()

    def get_password_hash(self, user_id):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""SELECT password_hash FROM users WHERE id = ?""", (user_id,))
        result = cursor.fetchone()
        conn.close()
        return result["password_hash"] if result else None

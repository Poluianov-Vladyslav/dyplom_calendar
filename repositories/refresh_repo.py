from database import get_connection

class RefreshTokenRepository:
    def save(self, user_id, token, expires_at):
        conn = get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO refresh_tokens (user_id, token, expires_at) VALUES (?, ?, ?)",
                (user_id, token, expires_at,))
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def get(self, token):
        conn = get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT user_id, expires_at FROM refresh_tokens WHERE token=?", (token,))
            result = cursor.fetchone()
            return result
        finally:
            conn.close()

    def delete(self, token):
        conn = get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM refresh_tokens WHERE token=?", (token,))
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

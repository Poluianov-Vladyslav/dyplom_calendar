from database import get_connection
from datetime import datetime


class NotificationRepository:
    def create(self, user_id, task_id, title, message, old_status, new_status):
        conn = get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""INSERT INTO notifications (user_id, task_id, title, message, old_status, new_status)
            VALUES (?, ?, ?, ?, ?, ?)""", (user_id, task_id, title, message, old_status, new_status))
            conn.commit()
            return cursor.lastrowid
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def get_unread_by_user(self, user_id):
        conn = get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""SELECT * FROM notifications 
            WHERE user_id = ? AND is_read = 0 
            ORDER BY created_at DESC""", (user_id,))
            return cursor.fetchall()
        finally:
            conn.close()

    def mark_as_read(self, notification_id, user_id):
        conn = get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""UPDATE notifications SET is_read = 1 
            WHERE id = ? AND user_id = ?""", (notification_id, user_id))
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def mark_all_as_read(self, user_id):
        conn = get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""UPDATE notifications SET is_read = 1 
            WHERE user_id = ? AND is_read = 0""", (user_id,))
            conn.commit()
            return cursor.rowcount
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def delete_old_notifications(self, user_id, days=30):
        conn = get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""DELETE FROM notifications WHERE user_id = ?
            AND created_at < datetime('now', ?)""", (user_id, f'-{days} days'))
            conn.commit()
            return cursor.rowcount
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
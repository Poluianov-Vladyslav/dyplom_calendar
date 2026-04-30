from database import get_connection

class TaskRepository:

    def create(self, user_id, title, description, plan_start, plan_end, priority):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO tasks (
                user_id, title, description, plan_start_time, plan_end_time, priority)
            VALUES (?, ?, ?, ?, ?, ?)""", (user_id, title, description, plan_start, plan_end, priority,))
        conn.commit()
        task_id = cursor.lastrowid
        conn.close()
        return task_id

    def get_tasks(self, user_id):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM tasks WHERE user_id = ? ORDER BY plan_start_time DESC""", (user_id,))
        tasks = cursor.fetchall()
        conn.close()
        return tasks

    def get_in_range(self, user_id, start, end):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM tasks WHERE user_id = ? AND (plan_start_time < ? AND plan_end_time > ?)""", (user_id, end, start,))
        tasks = cursor.fetchall()
        conn.close()
        return tasks

    def delete(self, user_id, task_id):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""DELETE FROM tasks WHERE user_id = ? AND id = ?""", (user_id, task_id))
        conn.commit()
        deleted = cursor.rowcount
        conn.close()
        return deleted > 0
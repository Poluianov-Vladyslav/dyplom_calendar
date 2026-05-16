from database import get_connection
from datetime import datetime

class TaskRepository:

    def create(self, user_id, title, description, plan_start, plan_end, priority, difficulty):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""INSERT INTO tasks (
            user_id, title, description, plan_start_time, plan_end_time, priority, difficulty)
            VALUES (?, ?, ?, ?, ?, ?, ?)""", (user_id, title, description, plan_start, plan_end, priority, difficulty,))
        conn.commit()
        task_id = cursor.lastrowid

        conn.close()
        return task_id

    def get_tasks(self, user_id):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""SELECT * FROM tasks WHERE user_id = ? ORDER BY plan_start_time DESC""", (user_id,))
        tasks = cursor.fetchall()
        conn.close()
        return tasks

    def get_by_id(self, task_id, user_id):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""SELECT * FROM tasks WHERE id = ? AND user_id = ?""", (task_id, user_id))
        task = cursor.fetchone()

        conn.close()
        return task

    def get_in_range(self, user_id, start, end):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""SELECT * FROM tasks WHERE user_id = ? AND (plan_start_time < ? AND plan_end_time > ?)""", (user_id, end, start,))
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

    def update(self, user_id, task_id, title, description, plan_start, plan_end, priority, difficulty):

        now = datetime.now()
        plan_end_dt = datetime.fromisoformat(plan_end)
        if plan_end_dt < now:
            status = "missed"
        else:
            status = "planning"

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE tasks SET title = ?, description = ?, plan_start_time = ?, plan_end_time = ?, priority = ?, difficulty = ?, status = ?
            WHERE id = ? AND user_id = ?""", (title, description, plan_start, plan_end, priority, difficulty, status, task_id, user_id))

        conn.commit()
        updated = cursor.rowcount
        conn.close()
        return updated > 0

    def start_task(self, user_id, task_id):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""SELECT id, status FROM tasks WHERE id = ? AND user_id = ?""", (task_id, user_id))
        task = cursor.fetchone()

        if not task:
            conn.close()
            return False
        if task["status"] != "planning":
            conn.close()
            return False

        cursor.execute("""UPDATE tasks SET status = 'in_progress' WHERE id = ? AND user_id = ?""", (task_id, user_id))
        cursor.execute("""INSERT OR REPLACE INTO task_statistics (task_id, actual_start_time) VALUES (?, ?)""", (task_id, datetime.now().isoformat()))
        conn.commit()
        conn.close()
        return True

    def complete_task(self, task_id, user_id, pleasure, productivity_score):
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""SELECT t.status, ts.actual_start_time FROM task_statistics ts
            JOIN tasks t ON t.id = ts.task_id WHERE ts.task_id = ? AND t.user_id = ?""", (task_id, user_id))

        stat = cursor.fetchone()
        if not stat:
            conn.close()
            return False

        if stat["status"] not in ["in_progress", "late"]:
            conn.close()
            return False

        if not stat["actual_start_time"]:
            conn.close()
            return False

        actual_start = datetime.fromisoformat(stat["actual_start_time"])
        completed_at = datetime.now()
        actual_time = int((completed_at - actual_start).total_seconds() / 60)
        completed_at_str = completed_at.isoformat()

        cursor.execute("""UPDATE tasks SET status = 'done' WHERE id = ? AND user_id = ?""", (task_id, user_id))
        cursor.execute("""UPDATE task_statistics SET completed_at = ?, actual_time = ?, pleasure = ?, productivity_score = ? WHERE task_id = ?""",
                       (completed_at_str, actual_time, pleasure, productivity_score, task_id))
        conn.commit()
        conn.close()
        return True

    def update_miss_and_late_tasks(self, user_id):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""UPDATE tasks SET status = 'missed' 
        WHERE user_id=? AND status IN ('planning') AND plan_end_time<?""", (user_id, datetime.now().isoformat()))

        cursor.execute("""UPDATE tasks SET status = 'late' 
                WHERE user_id=? AND status IN ('in_progress') AND plan_end_time<?""",
                       (user_id, datetime.now().isoformat()))
        conn.commit()
        conn.close()
        return True

    def get_analytics_data(self, user_id):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT t.id, t.title, t.priority, t.difficulty, t.status,
            t.plan_start_time, t.plan_end_time, t.created_at,
            ts.actual_start_time, ts.completed_at, ts.actual_time,
            ts.pleasure, ts.productivity_score
            FROM tasks t LEFT JOIN task_statistics ts ON ts.task_id = t.id
            WHERE t.user_id = ?
            ORDER BY t.created_at DESC""", (user_id,))
        tasks = cursor.fetchall()
        conn.close()
        return [dict(task) for task in tasks]

    def get_tasks_by_status(self, user_id):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""SELECT status, COUNT(*) as count
        FROM tasks WHERE user_id = ? GROUP BY status""", (user_id,))
        stats = cursor.fetchall()
        conn.close()
        return {stat["status"]: stat["count"] for stat in stats}

    def get_tasks_by_priority(self, user_id):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""SELECT priority, COUNT(*) as count FROM tasks
        WHERE user_id = ? GROUP BY priority ORDER BY priority""", (user_id,))
        stats = cursor.fetchall()
        conn.close()
        return {stat["priority"]: stat["count"] for stat in stats}

    def get_tasks_by_difficulty(self, user_id):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""SELECT difficulty, COUNT(*) as count FROM tasks
        WHERE user_id = ? GROUP BY difficulty ORDER BY difficulty""", (user_id,))
        stats = cursor.fetchall()
        conn.close()
        return {stat["difficulty"]: stat["count"] for stat in stats}




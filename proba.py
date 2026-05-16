from database import get_connection
conn = get_connection()
cursor = conn.cursor()
cursor.execute("SELECT id, status, user_id FROM tasks WHERE id = 3")
task = cursor.fetchone()
print(task)
conn.close()
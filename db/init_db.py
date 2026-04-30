from database import get_connection

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS refresh_tokens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            token TEXT UNIQUE NOT NULL,
            expires_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            plan_start_time TEXT NOT NULL,
            plan_end_time TEXT NOT NULL,
            actual_start_time TEXT,
            completed_at TEXT,
            actual_time INTEGER DEFAULT 0,
            priority INTEGER CHECK(priority BETWEEN 1 AND 5),
            progress INTEGER DEFAULT 0 CHECK(progress BETWEEN 0 AND 100),
            status TEXT DEFAULT 'planning' CHECK(status IN ('planning', 'in_progress', 'done', 'missed')),
            difficulty INTEGER CHECK(difficulty BETWEEN 1 AND 5),
            pleasure INTEGER CHECK(pleasure BETWEEN 1 AND 5),
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
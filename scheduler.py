import threading
from datetime import datetime
from services.task_service import TaskService
from repositories.users_repo import UserRepository
from services.notification_service import NotificationService

class BackgroundScheduler:
    def __init__(self):
        self.task_service = TaskService()
        self.notification_service = NotificationService()
        self.user_repo = UserRepository()
        self.stop_event = threading.Event()
        self.thread = None

    def update_all_statuses(self):
        try:
            users = self.user_repo.get_all_users()
            if not users:
                return

            for user in users:
                changed = self.task_service.update_missed_and_late_tasks(user["id"])

        except Exception as e:
            print(f"[{datetime.now()}] Помилка: {e}")

    def clean_old_notifications(self):
        try:
            users = self.user_repo.get_all_users()
            if not users:
                return

            total_deleted = 0
            for user in users:
                deleted = self.notification_service.delete_old(user["id"], days=30)
                total_deleted += deleted

        except Exception as e:
            print(f"[{datetime.now()}] Помилка очищення сповіщень: {e}")

    def run(self):
        print(f"[{datetime.now()}] Фоновий процес запущено")
        cycle_count = 0
        while not self.stop_event.is_set():
            self.update_all_statuses()

            cycle_count += 1
            if cycle_count >= 288:
                self.clean_old_notifications()
                cycle_count = 0

            self.stop_event.wait(300)

    def start(self):
        if self.thread is None or not self.thread.is_alive():
            self.stop_event.clear()
            self.thread = threading.Thread(target=self.run, daemon=True)
            self.thread.start()

    def stop(self):
        self.stop_event.set()
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=5)


scheduler = BackgroundScheduler()

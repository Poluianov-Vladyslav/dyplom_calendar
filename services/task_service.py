from repositories.task_repo import TaskRepository
from datetime import datetime

class TaskService:
    def __init__(self):
        self.repo = TaskRepository()

    def create(self, user_id, title, description, plan_start, plan_end, priority):
        try:
            start = datetime.fromisoformat(plan_start)
            end = datetime.fromisoformat(plan_end)
        except ValueError:
            raise ValueError("Невірний формат дати")
        if end <= start:
            raise ValueError("Час завершення має бути після початку")
        existing_tasks = self.repo.get_in_range(user_id, start.isoformat(), end.isoformat())
        if existing_tasks:
            conflicts = [
                {
                    "id": task["id"],
                    "title": task["title"],
                    "start": task["plan_start_time"],
                    "end": task["plan_end_time"]
                }
                for task in existing_tasks
            ]
            raise ValueError(f"Конфлікт задач по часу: {conflicts}")
        task_id = self.repo.create(
            user_id=user_id,
            title=title,
            description=description,
            plan_start=start.isoformat(),
            plan_end=end.isoformat(),
            priority=priority
        )
        return task_id

    def get_all_user_tasks(self, user_id):
        return self.repo.get_tasks(user_id)

    def get_by_day(self, user_id, date):
        try:
            target_date=datetime.fromisoformat(date)
            start_date = target_date.replace(hour=0, minute=0, second=0)
            end_day = target_date.replace(hour=23, minute=59, second=59)
            tasks = self.repo.get_in_range(user_id, start_date.isoformat(), end_day.isoformat())
            return [dict(task) for task in tasks]
        except ValueError:
            raise ValueError("Невірний формат дати. Використовуйте YYYY-MM-DD")

    def delete(self, user_id, task_id):
        return self.repo.delete(user_id, task_id)
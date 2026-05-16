from repositories.task_repo import TaskRepository
from datetime import datetime


class TaskService:
    def __init__(self):
        self.repo = TaskRepository()

    def create(self, user_id, title, description, plan_start, plan_end, priority, difficulty):
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
            priority=priority,
            difficulty = difficulty
        )
        return task_id

    def get_all_user_tasks(self, user_id):
        return self.repo.get_tasks(user_id)

    def update(self, task_id, user_id, title, description, plan_start, plan_end, priority, difficulty):
        try:
            start = datetime.fromisoformat(plan_start)
            end = datetime.fromisoformat(plan_end)
        except ValueError:
            raise ValueError("Невірний формат дати")

        if end <= start:
            raise ValueError("Час завершення має бути після початку")

        existing_task = self.repo.get_by_id(task_id, user_id)
        if not existing_task:
            raise ValueError("Задачу не знайдено")
        conflicts = self.repo.get_in_range(
            user_id,
            start.isoformat(),
            end.isoformat()
        )
        conflicts = [task for task in conflicts if task["id"] != task_id]
        if conflicts:
            raise ValueError("Конфлікт задач по часу")

        success = self.repo.update(
            task_id=task_id,
            user_id=user_id,
            title=title,
            description=description,
            plan_start=start.isoformat(),
            plan_end=end.isoformat(),
            priority=priority,
            difficulty=difficulty
        )
        return success

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

    def start_task(self, user_id, task_id):
        task = self.repo.get_by_id(task_id, user_id)
        if not task:
            raise ValueError("Задачу не знайдено")
        if task["status"] != "planning":
            raise ValueError("Задачу вже розпочато")

        success = self.repo.start_task(user_id, task_id)
        return success

    def complete_task(self, user_id, task_id, pleasure, productivity_score):
        task = self.repo.get_by_id(task_id, user_id)
        if not task:
            raise ValueError("Задачу не знайдено")
        if task["status"] != "in_progress":
            raise ValueError("Задача має бути у статусі in_progress")
        if pleasure < 1 or pleasure > 5:
            raise ValueError("pleasure має бути 1-5")
        if productivity_score < 0 or productivity_score > 100:
            raise ValueError("productivity_score має бути 0-100")

        success = self.repo.complete_task(
            task_id=task_id,
            user_id=user_id,
            pleasure=pleasure,
            productivity_score=productivity_score
        )
        return success

    def update_missed_and_late_tasks(self, user_id):
        return self.repo.update_miss_and_late_tasks(user_id)
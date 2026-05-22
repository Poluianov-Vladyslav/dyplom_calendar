from datetime import datetime
from typing import List, Dict, Any
from repositories.notification_repo import NotificationRepository


class NotificationService:
    def __init__(self):
        self.repo = NotificationRepository()

    def create_notification(self, user_id: int, task_id: int, title: str, old_status: str, new_status: str) -> Dict[str, Any]:
        status_names = {
            "planning": "📝 Заплановано",
            "in_progress": "⏳ В процесі",
            "done": "✅ Виконано",
            "missed": "❌ Пропущено",
            "late": "⚠️ Прострочено"
        }

        old_name = status_names.get(old_status, old_status)
        new_name = status_names.get(new_status, new_status)
        message = f"Статус задачі '{title}' змінено з {old_name} на {new_name}"
        notification_id = self.repo.create(
            user_id=user_id,
            task_id=task_id,
            title=title,
            message=message,
            old_status=old_status,
            new_status=new_status
        )
        return {
            "id": notification_id,
            "user_id": user_id,
            "task_id": task_id,
            "title": title,
            "message": message,
            "old_status": old_status,
            "new_status": new_status,
            "created_at": datetime.now().isoformat()
        }

    def create_batch_notifications(self, changes: List[Dict], user_id: int) -> List[Dict]:
        notifications = []
        for change in changes:
            notification = self.create_notification(
                user_id=user_id,
                task_id=change["task_id"],
                title=change["title"],
                old_status=change["old_status"],
                new_status=change["new_status"]
            )
            notifications.append(notification)
        return notifications

    def get_unread(self, user_id: int) -> List[Dict]:
        return [dict(n) for n in self.repo.get_unread_by_user(user_id)]

    def mark_as_read(self, notification_id: int, user_id: int) -> bool:
        return self.repo.mark_as_read(notification_id, user_id)

    def mark_all_as_read(self, user_id: int) -> int:
        return self.repo.mark_all_as_read(user_id)

    def delete_old(self, user_id: int, days: int = 30) -> int:
        return self.repo.delete_old_notifications(user_id, days)

    def get_unread_count(self, user_id: int) -> int:
        return len(self.get_unread(user_id))
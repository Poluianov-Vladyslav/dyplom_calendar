from datetime import datetime, timedelta
from typing import Dict, List, Any
from repositories.task_repo import TaskRepository

class AnalyticsService:
    def __init__(self):
        self.repository = TaskRepository()

    def get_analytics(self, user_id: int) -> Dict[str, Any]:
        tasks = self.repository.get_analytics_data(user_id)
        status_stats = self.repository.get_tasks_by_status(user_id)
        priority_stats = self.repository.get_tasks_by_priority(user_id)
        difficulty_stats = self.repository.get_tasks_by_difficulty(user_id)

        basic_stats = self._get_basic_stats(tasks, status_stats)
        quality_stats = self._get_quality_stats(tasks)
        time_stats = self._get_time_stats(tasks)
        behavior_stats = self._get_behavior_stats(tasks)
        performance_stats = self._get_performance_stats(tasks)
        recommendations = self._get_recommendations(time_stats, behavior_stats, performance_stats)

        return {
            **basic_stats,
            **quality_stats,
            **time_stats,
            **behavior_stats,
            **performance_stats,
            "recommendations": recommendations,
        }

    def _get_basic_stats(self, tasks: List[Dict], status_stats: Dict) -> Dict[str, Any]:
        total = len(tasks)
        completed = status_stats.get("done", 0)
        in_progress = status_stats.get("in_progress", 0)
        planning = status_stats.get("planning", 0)
        missed = status_stats.get("missed", 0)
        late = status_stats.get("late", 0)
        completion_rate = round(completed / total * 100, 1) if total > 0 else 0

        return {
            "total": total,
            "completed": completed,
            "in_progress": in_progress,
            "planning": planning,
            "missed": missed,
            "late": late,
            "completion_rate": completion_rate,
        }

    def _get_quality_stats(self, tasks: List[Dict]) -> Dict[str, Any]:
        completed_tasks = [t for t in tasks if t.get("status") == "done" and t.get("productivity_score") is not None]
        avg_productivity_score = round(
            sum(t["productivity_score"] for t in completed_tasks) / len(completed_tasks), 1
        ) if completed_tasks else 0

        tasks_with_pleasure = [t for t in tasks if t.get("pleasure") is not None]
        avg_pleasure = round(
            sum(t["pleasure"] for t in tasks_with_pleasure) / len(tasks_with_pleasure), 1
        ) if tasks_with_pleasure else 0

        pleasure_productivity_correlation = self._get_pleasure_productivity_correlation(tasks)

        return {
            "avg_productivity_score": avg_productivity_score,
            "avg_pleasure": avg_pleasure,
            "pleasure_productivity_correlation": pleasure_productivity_correlation,
        }

    def _get_time_stats(self, tasks: List[Dict]) -> Dict[str, Any]:
        tasks_with_time = [t for t in tasks if t.get("actual_time") is not None]
        total_work_minutes = sum(t["actual_time"] for t in tasks_with_time)
        total_work_hours = round(total_work_minutes / 60, 1)

        weekly_performance = self._get_weekly_performance(tasks)
        hourly_performance = self._get_hourly_performance(tasks)
        average_delay = self._get_average_delay(tasks)
        planned_vs_actual = self._get_planned_vs_actual(tasks)

        return {
            "total_work_hours": total_work_hours,
            "weekly_performance": weekly_performance,
            "hourly_performance": hourly_performance,
            "average_delay": average_delay,
            "planned_vs_actual": planned_vs_actual,
        }

    def _get_behavior_stats(self, tasks: List[Dict]) -> Dict[str, Any]:
        timeline = self._get_timeline(tasks)
        completion_streak = self._get_completion_streak(tasks)

        completed_tasks = [
            t for t in tasks
            if t.get("status") == "done"
               and t.get("completed_at")
               and t.get("plan_end_time")
        ]
        late_completed = 0
        for task in completed_tasks:
            try:
                completed_at = datetime.fromisoformat(task["completed_at"])
                plan_end = datetime.fromisoformat(task["plan_end_time"])

                if completed_at > plan_end:
                    late_completed += 1
            except (ValueError, KeyError):
                continue
        overdue_ratio = round(late_completed / len(completed_tasks) * 100, 1) if completed_tasks else 0

        return {
            "timeline": timeline,
            "completion_streak": completion_streak,
            "overdue_ratio": overdue_ratio,
        }

    def _get_performance_stats(self, tasks: List[Dict]) -> Dict[str, Any]:
        difficulty_productivity = self._get_difficulty_productivity(tasks)
        return {
            "difficulty_productivity": difficulty_productivity,
        }

    def _get_weekly_performance(self, tasks: List[Dict]) -> List[Dict]:
        days_order = ["Понеділок", "Вівторок", "Середа", "Четвер", "П'ятниця", "Субота", "Неділя"]
        day_data = {day: {
            "total_tasks": 0,
            "completed": 0,
            "sum_productivity": 0,
            "productivity_count": 0,
            "sum_pleasure": 0,
            "pleasure_count": 0,
            "sum_time": 0,
            "time_count": 0
        } for day in days_order}

        for task in tasks:
            if task.get("plan_start_time"):
                try:
                    plan_date = datetime.fromisoformat(task["plan_start_time"])
                    day_name = days_order[plan_date.weekday()]
                    day_data[day_name]["total_tasks"] += 1
                except (ValueError, KeyError):
                    pass
            if task.get("status") == "done" and task.get("completed_at"):
                try:
                    completed_date = datetime.fromisoformat(task["completed_at"])
                    day_name = days_order[completed_date.weekday()]
                    day_data[day_name]["completed"] += 1

                    if task.get("productivity_score") is not None:
                        day_data[day_name]["sum_productivity"] += task["productivity_score"]
                        day_data[day_name]["productivity_count"] += 1

                    if task.get("pleasure") is not None:
                        day_data[day_name]["sum_pleasure"] += task["pleasure"]
                        day_data[day_name]["pleasure_count"] += 1

                    if task.get("actual_time") is not None:
                        day_data[day_name]["sum_time"] += task["actual_time"]
                        day_data[day_name]["time_count"] += 1

                except (ValueError, KeyError):
                    pass

        result = []
        for day in days_order:
            data = day_data[day]

            avg_productivity = round(data["sum_productivity"] / data["productivity_count"], 1) if data[
                                                                                                      "productivity_count"] > 0 else 0
            avg_pleasure = round(data["sum_pleasure"] / data["pleasure_count"], 1) if data["pleasure_count"] > 0 else 0
            avg_time = round(data["sum_time"] / data["time_count"], 0) if data["time_count"] > 0 else 0
            completion_rate = round(data["completed"] / data["total_tasks"] * 100, 1) if data["total_tasks"] > 0 else 0

            result.append({
                "day": day,
                "total_tasks": data["total_tasks"],
                "completed": data["completed"],
                "completion_rate": completion_rate,
                "avg_productivity": avg_productivity,
                "avg_pleasure": avg_pleasure,
                "avg_time": avg_time
            })

        return result

    def _get_hourly_performance(self, tasks: List[Dict]) -> List[Dict]:
        productivity_sum = {}
        productivity_count = {}
        for task in tasks:
            if task.get("actual_start_time") and task.get("productivity_score") is not None:
                try:
                    actual_start = datetime.fromisoformat(task["actual_start_time"])
                    hour = actual_start.hour
                    productivity_sum[hour] = productivity_sum.get(hour, 0) + task["productivity_score"]
                    productivity_count[hour] = productivity_count.get(hour, 0) + 1
                except (ValueError, KeyError):
                    continue
        result = []
        for hour in range(24):
            count = productivity_count.get(hour, 0)
            if count > 0:
                avg = round(productivity_sum[hour] / count, 1)
            else:
                avg = 0
            result.append({"hour": hour, "avg_productivity": avg})

        return result

    def _get_timeline(self, tasks: List[Dict]) -> List[Dict]:
        today = datetime.now().date()
        timeline = []
        for i in range(29, -1, -1):
            date = today - timedelta(days=i)
            date_str = date.isoformat()
            completed = 0
            for task in tasks:
                if task.get("status") != "done" or not task.get("completed_at"):
                    continue
                try:
                    completed_date = datetime.fromisoformat(task["completed_at"]).date()
                    if completed_date == date:
                        completed += 1
                except (ValueError, KeyError):
                    continue
            timeline.append({"date": date_str, "count": completed})
        return timeline

    def _get_difficulty_productivity(self, tasks: List[Dict]) -> List[Dict]:
        difficulty_data = {1: [], 2: [], 3: [], 4: [], 5: []}
        for task in tasks:
            diff = task.get("difficulty")
            prod = task.get("productivity_score")
            if diff in range(1, 6) and prod is not None:
                difficulty_data[diff].append(prod)
        result = []
        for diff in range(1, 6):
            avg = round(sum(difficulty_data[diff]) / len(difficulty_data[diff]), 1) if difficulty_data[diff] else 0
            result.append({"difficulty": diff, "avg_productivity": avg})
        return result

    def _get_pleasure_productivity_correlation(self, tasks: List[Dict]) -> List[Dict]:
        pleasure_data = {1: [], 2: [], 3: [], 4: [], 5: []}
        for task in tasks:
            pleasure = task.get("pleasure")
            productivity = task.get("productivity_score")
            if pleasure in range(1, 6) and productivity is not None:
                pleasure_data[pleasure].append(productivity)
        result = []
        for pleasure in range(1, 6):
            avg = round(sum(pleasure_data[pleasure]) / len(pleasure_data[pleasure]), 1) if pleasure_data[
                pleasure] else 0
            result.append({"pleasure": pleasure, "avg_productivity": avg})
        return result

    def _get_completion_streak(self, tasks: List[Dict]) -> Dict[str, Any]:
        completion_dates = set()
        for task in tasks:
            if task.get("status") == "done" and task.get("completed_at"):
                try:
                    date = datetime.fromisoformat(task["completed_at"]).date()
                    completion_dates.add(date)
                except (ValueError, KeyError):
                    continue

        if not completion_dates:
            return {"current_streak": 0, "longest_streak": 0, "message": "Немає виконаних задач"}
        sorted_dates = sorted(completion_dates)
        today = datetime.now().date()
        current_streak = 0
        check_date = today

        while check_date in completion_dates:
            current_streak += 1
            check_date -= timedelta(days=1)
        longest_streak = 1
        current = 1
        for i in range(1, len(sorted_dates)):
            if (sorted_dates[i] - sorted_dates[i - 1]).days == 1:
                current += 1
                longest_streak = max(longest_streak, current)
            else:
                current = 1
        return {
            "current_streak": current_streak,
            "longest_streak": longest_streak,
            "message": f"Найдовша серія: {longest_streak} днів"
        }

    def _get_average_delay(self, tasks: List[Dict]) -> Dict[str, Any]:
        delays = []
        now = datetime.now()
        for task in tasks:
            plan_end = task.get("plan_end_time")
            if not plan_end:
                continue
            try:
                plan_end_dt = datetime.fromisoformat(plan_end)
                if task.get("status") == "done" and task.get("completed_at"):
                    completed_dt = datetime.fromisoformat(task["completed_at"])
                    if completed_dt > plan_end_dt:
                        delay_minutes = int((completed_dt - plan_end_dt).total_seconds() / 60)
                        delays.append(delay_minutes)
            except (ValueError, KeyError):
                continue
        if not delays:
            return {
                "average_delay_minutes": 0,
                "average_delay_hours": 0,
                "total_delayed_tasks": 0,
                "message": "Немає прострочених задач"
            }

        avg_delay = round(sum(delays) / len(delays), 0)

        return {
            "average_delay_minutes": avg_delay,
            "average_delay_hours": round(avg_delay / 60, 1),
            "total_delayed_tasks": len(delays),
            "message": f"Середнє запізнення: {avg_delay} хвилин"
        }

    def _get_planned_vs_actual(self, tasks: List[Dict]) -> Dict[str, Any]:
        planned_vs_actual = []
        for task in tasks:
            if task.get("status") != "done":
                continue
            plan_start = task.get("plan_start_time")
            plan_end = task.get("plan_end_time")
            actual_time = task.get("actual_time")
            if plan_start is None or plan_end is None or actual_time is None:
                continue
            try:
                start_dt = datetime.fromisoformat(plan_start)
                end_dt = datetime.fromisoformat(plan_end)
                planned_minutes = int((end_dt - start_dt).total_seconds() / 60)

                if planned_minutes > 0:
                    ratio = round(actual_time / planned_minutes, 2)
                    planned_vs_actual.append({
                        "planned": planned_minutes,
                        "actual": actual_time,
                        "ratio": ratio,
                        "difference": actual_time - planned_minutes
                    })
            except (ValueError, KeyError):
                continue
        if not planned_vs_actual:
            return {
                "average_planned_minutes": 0,
                "average_actual_minutes": 0,
                "average_efficiency_ratio": 0,
                "total_tasks_analyzed": 0,
                "message": "Немає даних для порівняння"
            }
        avg_planned = round(sum(p["planned"] for p in planned_vs_actual) / len(planned_vs_actual), 0)
        avg_actual = round(sum(p["actual"] for p in planned_vs_actual) / len(planned_vs_actual), 0)
        avg_ratio = round(sum(p["ratio"] for p in planned_vs_actual) / len(planned_vs_actual), 2)
        if avg_ratio > 1.2:
            efficiency_desc = "Користувач систематично недооцінює час"
        elif avg_ratio < 0.8:
            efficiency_desc = "Користувач систематично переоцінює час"
        else:
            efficiency_desc = "Час оцінюється досить точно"
        return {
            "average_planned_minutes": avg_planned,
            "average_actual_minutes": avg_actual,
            "average_efficiency_ratio": avg_ratio,
            "total_tasks_analyzed": len(planned_vs_actual),
            "efficiency_desc": efficiency_desc,
            "data": planned_vs_actual[:10]
        }

    def _get_recommendations(self, time_stats: Dict, behavior_stats: Dict, performance_stats: Dict) -> List[Dict]:
        weekly_performance = time_stats.get("weekly_performance", [])
        hourly_performance = time_stats.get("hourly_performance", [])
        average_delay = time_stats.get("average_delay", {})
        planned_vs_actual = time_stats.get("planned_vs_actual", {})
        completion_streak_data = behavior_stats.get("completion_streak", {})
        recommendations = []

        if weekly_performance:
            best_day = max(weekly_performance, key=lambda x: x["avg_productivity"])
            worst_day = min(weekly_performance, key=lambda x: x["avg_productivity"])

            recommendations.append({
                "type": "day",
                "title": "Ваш найпродуктивніший день",
                "message": f"Найкраще ви працюєте у {best_day['day']}!",
                "detail": f"Ваша середня продуктивність у цей день становить {best_day['avg_productivity']}%.",
                "suggestion": f"Плануйте найскладніші задачі на {best_day['day']}."
            })

            recommendations.append({
                "type": "day_warning",
                "title": "День з найнижчою продуктивністю",
                "message": f"У {worst_day['day']} ваша продуктивність найнижча ({worst_day['avg_productivity']}%).",
                "suggestion": f"Плануйте легкі задачі або відпочинок на {worst_day['day']}."
            })

        if hourly_performance:
            best_hour_data = max(hourly_performance, key=lambda x: x["avg_productivity"])
            start_hour = best_hour_data["hour"]
            end_hour = start_hour + 2
            if end_hour > 23:
                end_hour = 23
            recommendations.append({
                "type": "time",
                "title": "Ваш найпродуктивніший час",
                "message": f"Найкраще ви працюєте з {start_hour}:00 до {end_hour}:00!",
                "detail": f"У цей час ваша продуктивність досягає {best_hour_data['avg_productivity']}%.",
                "suggestion": "Плануйте важливі та складні задачі на цей час."
            })

        delay_mins = average_delay['average_delay_minutes']
        buffer_time = max(15, (delay_mins // 15) * 15)
        recommendations.append({
            "type": "delay",
            "title": "Покращення планування часу",
            "message": f"Ваші задачі в середньому запізнюються на {delay_mins} хвилин.",
            "detail": f"Ви маєте {average_delay['total_delayed_tasks']} прострочених задач.",
            "suggestion": f"Додавайте +{buffer_time} хвилин запасу при плануванні кожної задачі."
        })

        ratio = planned_vs_actual.get("average_efficiency_ratio", 0)
        if ratio > 1.2:
            over_percent = round((ratio - 1) * 100)
            recommendations.append({
                "type": "estimation",
                "title": "Точність оцінювання часу",
                "message": f"Ви недооцінюєте час на задачі в середньому на {over_percent}%.",
                "detail": f"Заплановано: {planned_vs_actual['average_planned_minutes']} хв, "
                          f"фактично: {planned_vs_actual['average_actual_minutes']} хв.",
                "suggestion": f"Помножуйте вашу оцінку часу на {round(ratio, 1)} для більшої точності."
            })
        elif 0 < ratio < 0.8:
            under_percent = round((1 - ratio) * 100)
            recommendations.append({
                "type": "estimation",
                "title": "Точність оцінювання часу",
                "message": f"Ви переоцінюєте час на задачі в середньому на {under_percent}%.",
                "detail": f"Заплановано: {planned_vs_actual['average_planned_minutes']} хв, "
                          f"фактично: {planned_vs_actual['average_actual_minutes']} хв.",
                "suggestion": f"Спробуйте зменшити оцінку часу на {under_percent}%."
            })
        if completion_streak_data.get("current_streak", 0) > 3:
            recommendations.append({
                "type": "streak",
                "title": "Серія успіху",
                "message": f"Ви виконуєте задачі {completion_streak_data['current_streak']} днів поспіль!",
                "detail": f"Ваша найдовша серія: {completion_streak_data['longest_streak']} днів.",
                "suggestion": "Не зупиняйтесь! Щоденне планування – ключ до успіху."
            })
        difficulty_productivity = performance_stats.get("difficulty_productivity", [])
        high_diff = [d for d in difficulty_productivity if d["difficulty"] >= 4 and d["avg_productivity"] > 0]
        low_diff = [d for d in difficulty_productivity if d["difficulty"] <= 2 and d["avg_productivity"] > 0]

        if high_diff and low_diff:
            best_high = max(high_diff, key=lambda x: x["avg_productivity"])
            if best_high["avg_productivity"] > 70:
                recommendations.append({
                    "type": "difficulty_success",
                    "title": "Робота зі складними задачами",
                    "message": f"Складні задачі (рівень {best_high['difficulty']}) ви виконуєте з продуктивністю {best_high['avg_productivity']}%!",
                    "suggestion": "Не бійтесь братися за складні завдання – у вас добре виходить."
                })
        elif low_diff:
            best_low = max(low_diff, key=lambda x: x["avg_productivity"])
            if best_low["avg_productivity"] > 80:
                recommendations.append({
                    "type": "difficulty_easy",
                    "title": "Робота з легкими задачами",
                    "message": f"Легкі задачі ви виконуєте з продуктивністю {best_low['avg_productivity']}%!",
                    "suggestion": "Спробуйте поступово підвищувати складність задач."
                })

        if not recommendations:
            recommendations.append({
                "type": "general",
                "title": "Порада дня",
                "message": "Продовжуйте працювати в тому ж ритмі!",
                "detail": "Ви добре організовуєте свій час.",
                "suggestion": "Спробуйте вести щоденник продуктивності для ще кращих результатів."
            })
        return recommendations
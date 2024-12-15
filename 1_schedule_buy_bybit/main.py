import os
import asyncio
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.date import DateTrigger
from bd.schedule import ScheduleOperations
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv('database_url')

async def before_task():
    print(f"Before task executed at {datetime.now()}")

async def main_task():
    print(f"Main task executed at {datetime.now()}")

async def schedule_tasks(scheduler, schedule_data):
    now = datetime.now()
    current_day = now.isoweekday()
    next_day = (current_day % 7) + 1  # Следующий день недели

    scheduler.remove_all_jobs()
    # print("All previous tasks removed.")

    # Проверяем, является ли schedule_data списком или словарём
    if isinstance(schedule_data, dict):
        schedule_data = [schedule_data]  # Преобразуем в список для унификации обработки

    for schedule in schedule_data:
        week_days = schedule["week_day"]
        task_time = datetime.strptime(schedule["time"], "%H:%M:%S").time()

        for day in week_days:
            if day == current_day:
                task_date = now.date()
                task_datetime = datetime.combine(task_date, task_time)

                # Проверяем, нужно ли планировать задачу на сегодня
                if task_datetime <= now:
                    continue  # Задача на сегодня уже прошла, пропускаем

            elif day == next_day:
                # Проверяем, нужно ли планировать задачу на следующий день
                task_date = now.date() + timedelta(days=1)
                task_datetime = datetime.combine(task_date, task_time)

            else:
                continue  # Пропускаем задачи для других дней

            # меняем minutes=3 в зависимости от сложности предварнительного запроса и лимитов биржи
            before_task_time = task_datetime - timedelta(minutes=3)

            before_task_id = f"before_task_{day}_{task_time}"
            main_task_id = f"main_task_{day}_{task_time}"

            # Пропускаем задачи, если их время уже прошло
            if before_task_time <= now and task_datetime <= now:
                continue

            # Добавляем задачи в планировщик
            if before_task_time > now:
                scheduler.add_job(
                    before_task,
                    DateTrigger(run_date=before_task_time),
                    id=before_task_id,
                    replace_existing=True,
                )
                print(f"Before task scheduled for {before_task_time}")

            if task_datetime > now:
                scheduler.add_job(
                    main_task,
                    DateTrigger(run_date=task_datetime),
                    id=main_task_id,
                    replace_existing=True,
                )
                print(f"Main task scheduled for {task_datetime}")


async def main():
    scheduler = AsyncIOScheduler()
    scheduler.start()
    schedule_op = ScheduleOperations(DATABASE_URL)

    while True:
        schedule = await schedule_op.get_schedule()

        if schedule:
            print(f"Current schedule: {schedule}")
            await schedule_tasks(scheduler, schedule)

        await asyncio.sleep(60)  # Проверяем расписание каждую минуту

# Запуск
if __name__ == "__main__":
    asyncio.run(main())

import os
import asyncio
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.date import DateTrigger
from bd.schedule import ScheduleOperations
from bd.settings import SettingsOperations
from bd.users import UsersOperations
from dotenv import load_dotenv

from strategy import pre_task, main_task

load_dotenv()

DATABASE_URL = os.getenv('database_url')

async def schedule_tasks(scheduler, schedule_data, task_queue):
    now = datetime.now()
    current_day = now.isoweekday()
    next_day = (current_day % 7) + 1

    scheduler.remove_all_jobs()

    if isinstance(schedule_data, dict):
        schedule_data = [schedule_data]

    for schedule in schedule_data:
        week_days = schedule["week_day"]
        task_time = datetime.strptime(schedule["time"], "%H:%M:%S").time()

        for day in week_days:
            if day == current_day:
                task_date = now.date()
                task_datetime = datetime.combine(task_date, task_time)
                if task_datetime <= now:
                    continue
            elif day == next_day:
                task_date = now.date() + timedelta(days=1)
                task_datetime = datetime.combine(task_date, task_time)
            else:
                continue

            before_task_time = task_datetime - timedelta(minutes=3)

            if before_task_time > now:
                scheduler.add_job(
                    pre_task_wrapper,
                    DateTrigger(run_date=before_task_time),
                    kwargs={"task_queue": task_queue},
                )
                print(f"Pre-task scheduled for {before_task_time}")

            if task_datetime > now:
                scheduler.add_job(
                    main_task_wrapper,
                    DateTrigger(run_date=task_datetime),
                    kwargs={"task_queue": task_queue},
                )
                print(f"Main task scheduled for {task_datetime}")


async def pre_task_wrapper(task_queue):
    settings_op = SettingsOperations(DATABASE_URL)
    users_op = UsersOperations(DATABASE_URL)

    # Выполняем pre_task и добавляем данные в очередь
    data = await pre_task(settings_op, users_op)
    await task_queue.put(data)
    print(f"Pre-task completed and data added to queue at {datetime.now()}")


async def main_task_wrapper(task_queue):
    # Получаем данные из очереди
    data = await task_queue.get()
    if data:
        BTCUSDT_settings, ETHUSDT_settings, general_settings, valid_users, budgets, _ = data
        await main_task(BTCUSDT_settings, ETHUSDT_settings, general_settings, valid_users, budgets)
        print(f"Main task executed at {datetime.now()}")


async def main():
    scheduler = AsyncIOScheduler()
    scheduler.start()

    schedule_op = ScheduleOperations(DATABASE_URL)
    task_queue = asyncio.Queue()

    while True:
        schedule = await schedule_op.get_schedule()

        if schedule:
            print(f"Current schedule: {schedule}")
            await schedule_tasks(scheduler, schedule, task_queue)

        await asyncio.sleep(60)


if __name__ == "__main__":
    asyncio.run(main())

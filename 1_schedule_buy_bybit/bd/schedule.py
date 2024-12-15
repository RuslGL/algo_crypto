import os

from sqlalchemy import Column, String, JSON, DateTime, func
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.sql import text
import asyncio





Base = declarative_base()

class Schedule(Base):
    __tablename__ = 'schedule'

    id = Column(String, primary_key=True, default="singleton")  # Единственная запись
    week_day = Column(JSON, default=list)
    time = Column(String)  # Хранение времени в формате HH:MM:SS
    created = Column(DateTime, server_default=func.now())

class ScheduleOperations:
    def __init__(self, database_url: str):
        self.engine = create_async_engine(database_url, echo=False)
        self.async_session = sessionmaker(self.engine, class_=AsyncSession, expire_on_commit=False)

    async def table_exists(self, table_name: str) -> bool:
        async with self.engine.connect() as conn:
            result = await conn.scalar(
                text("SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = :table_name)"),
                {"table_name": table_name}
            )
            return result

    async def create_table(self):
        if not await self.table_exists(Schedule.__tablename__):
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            print(f"Table '{Schedule.__tablename__}' created successfully.")
        else:
            print(f"Table '{Schedule.__tablename__}' already exists, skipping creation.")

    async def upsert_schedule(self, week_day: list, hours: int, minutes: int):
        # Проверка данных
        if not all(isinstance(day, int) and 1 <= day <= 7 for day in week_day):
            print("Error: week_day must be a list of integers between 1 and 7.")
            return -1

        if not (0 <= hours <= 23):
            print("Error: hours must be between 0 and 23.")
            return -1

        if not (0 <= minutes <= 59):
            print("Error: minutes must be between 0 and 59.")
            return -1

        time_str = f"{hours:02}:{minutes:02}:00"

        async with self.async_session() as session:
            async with session.begin():
                stmt = insert(Schedule).values(
                    id="singleton",  # Единственная запись
                    week_day=week_day,
                    time=time_str
                ).on_conflict_do_update(
                    index_elements=['id'],
                    set_={"week_day": week_day, "time": time_str}
                )
                await session.execute(stmt)
            await session.commit()
        print(f"Upserted schedule with week_day={week_day} and time={time_str}.")

    async def get_schedule(self):
        async with self.async_session() as session:
            async with session.begin():
                result = await session.execute(text("SELECT week_day, time FROM schedule WHERE id='singleton'"))
                schedule = result.fetchone()
                if schedule:
                    return {"week_day": schedule[0], "time": schedule[1]}
                return None

# Тестовый запуск
if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv()

    DATABASE_URL = os.getenv('database_url')

    async def main():
        schedule_ops = ScheduleOperations(DATABASE_URL)

        await schedule_ops.create_table()


        await schedule_ops.upsert_schedule(week_day=[1, 3, 5], hours=15, minutes=30)

        schedule = await schedule_ops.get_schedule()
        print("Current schedule:", schedule)

    asyncio.run(main())


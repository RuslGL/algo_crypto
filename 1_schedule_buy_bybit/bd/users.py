import os
import asyncio
from dotenv import load_dotenv
from sqlalchemy import Column, String, Boolean, BigInteger, text, DateTime, func
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.future import select

import pandas as pd
from typing import Optional



load_dotenv()

DATABASE_URL = os.getenv('database_url')

BaseUsers = declarative_base()


class UserNotFoundError(Exception):
    pass


class Users(BaseUsers):

    __tablename__ = 'users'

    telegram_id = Column(BigInteger, primary_key=True, nullable=False)
    username = Column(String, nullable=True)
    stop_trading = Column(Boolean, default=False)
    created = Column(DateTime, server_default=func.now())

    # API keys
    api_key = Column(String, nullable=True)
    secret_key = Column(String, nullable=True)


class UsersOperations:
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
        if not await self.table_exists(Users.__tablename__):
            async with self.engine.begin() as conn:
                await conn.run_sync(BaseUsers.metadata.create_all)
            print(f"Table '{Users.__tablename__}' created successfully.")
        else:
            print(f"Table '{Users.__tablename__}' already exists, skipping creation.")


    async def create_table(self):
        if not await self.table_exists(Users.__tablename__):
            async with self.engine.begin() as conn:
                await conn.run_sync(BaseUsers.metadata.create_all)
            print(f"Table '{Users.__tablename__}' created successfully.")
        else:
            print(f"Table '{Users.__tablename__}' already exists, skipping creation.")

    async def get_all_users_data(self) -> Optional[pd.DataFrame]:
        async with self.async_session() as session:
            async with session.begin():
                query = select(Users)
                result = await session.execute(query)
                users = result.scalars().all()

                if users:
                    # Преобразование списка объектов в список словарей, затем в DataFrame
                    users_data = [user.__dict__ for user in users]
                    df = pd.DataFrame(users_data)
                    df = df.drop(columns="_sa_instance_state", errors='ignore')  # Удаление ненужного системного столбца
                    return df
                return None

    # async def upsert_user(self, user_data: dict):
    #     async with self.async_session() as session:
    #         async with session.begin():
    #             stmt = insert(Users).values(user_data).on_conflict_do_update(
    #                 index_elements=['telegram_id'],
    #                 set_=user_data
    #             )
    #             await session.execute(stmt)
    #         await session.commit()


    # async def delete_user(self, telegram_id: int):
    #     async with self.async_session() as session:
    #         async with session.begin():
    #             # Проверка наличия пользователя
    #             query_check = text("SELECT 1 FROM users WHERE telegram_id = :telegram_id")
    #             result_check = await session.execute(query_check, {"telegram_id": telegram_id})
    #             if result_check.scalar_one_or_none() is None:
    #                 raise UserNotFoundError(f"User with telegram_id {telegram_id} does not exist.")
    #
    #             # Выполнение удаления
    #             query_delete = text("DELETE FROM users WHERE telegram_id = :telegram_id")
    #             result_delete = await session.execute(query_delete, {"telegram_id": telegram_id})
    #             await session.commit()


if __name__ == '__main__':

    async def main():

        user_op = UsersOperations(DATABASE_URL)
        await user_op.create_table()


    asyncio.run(main())



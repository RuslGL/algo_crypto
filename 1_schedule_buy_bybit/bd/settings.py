import os
from dotenv import load_dotenv

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Column, BigInteger, String, Boolean, DateTime, select, update, insert, func, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.declarative import declarative_base
import asyncio


load_dotenv()

DATABASE_URL = os.getenv('database_url')

Base = declarative_base()

class Settings(Base):
    __tablename__ = 'settings'

    id = Column(BigInteger, primary_key=True, nullable=False, default=1)  # Fixed primary key value
    stop_trading = Column(Boolean, default=False)
    trading_pair = Column(String, nullable=False, default='BTCUSDT')
    razmer_posizii = Column(BigInteger, nullable=False, default=100)
    leverage = Column(BigInteger, nullable=False, default=1)
    teyk_profit = Column(BigInteger, nullable=False, default=1)


class SettingsOperations:
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
        if not await self.table_exists(Settings.__tablename__):
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            print(f"Table '{Settings.__tablename__}' created successfully.")
        else:
            print(f"Table '{Settings.__tablename__}' already exists, skipping creation.")

    async def get_all_settings(self):
        async with self.async_session() as session:
            query = select(Settings)
            result = await session.execute(query)
            settings = result.scalars().first()  # Fetch the single row if it exists

            if settings:
                return {
                    "name": 'trade_settings',
                    "stop_trading": settings.stop_trading,
                    "trading_pair": settings.trading_pair,
                    "razmer_posizii": settings.razmer_posizii,
                    "leverage": settings.leverage,
                    "teyk_profit": settings.teyk_profit,
                }

            return None

    async def upsert_settings(self, data: dict):
        async with self.async_session() as session:
            async with session.begin():
                try:
                    existing_row = await session.get(Settings, 1)
                    if existing_row:
                        for key, value in data.items():
                            setattr(existing_row, key, value)
                    else:
                        new_row = Settings(id=1, **data)
                        session.add(new_row)
                except IntegrityError as e:
                    print(f"Database integrity error: {e}")
                    raise


if __name__ == '__main__':

    async def main():

        settings_op = SettingsOperations(DATABASE_URL)
        await settings_op.create_table()

        await settings_op.upsert_settings({"trading_pair": "ETHUSDT"})

        settings = await settings_op.get_all_settings()
        print("Settings:", settings)

    asyncio.run(main())


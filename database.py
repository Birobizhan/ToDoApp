from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from environs import Env

env = Env()
env.read_env()
SQLALCHEMY_DATABASE_URL = env('SQLALCHEMY_DATABASE_URL')

engine = create_async_engine(SQLALCHEMY_DATABASE_URL, echo=True)
async_session = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()


async def get_db():
    db = async_session()
    try:
        yield db
    finally:
        await db.close()
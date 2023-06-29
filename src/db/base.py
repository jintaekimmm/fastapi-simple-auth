from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base

from core.config import settings

#########################
# SQLALCHEMY
#########################
SQLALCHEMY_DATABASE_URL = (
    f"mysql+asyncmy://{settings.db_user}:{settings.db_password}"
    f"@{settings.db_host}:{settings.db_port}/{settings.db_name}"
)

engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL, pool_recycle=300, pool_size=40, pool_pre_ping=True
)
async_session = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)

Base = declarative_base()


def show_raw_query(query):
    print(query.compile(engine, compile_kwargs={"literal_binds": True}))

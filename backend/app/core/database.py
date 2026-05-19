from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.core.config import settings

# 数据库引擎参数
engine_kwargs = {
    "echo": settings.DEBUG,
    "future": True,
}

# SQLite 需要额外配置
if settings.DATABASE_URL.startswith("sqlite"):
    engine_kwargs["connect_args"] = {"check_same_thread": False}

# 创建异步引擎
engine = create_async_engine(
    settings.DATABASE_URL,
    **engine_kwargs,
)

# 创建异步会话工厂
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """所有模型的基类"""
    pass


async def get_db():
    """获取数据库会话的依赖"""
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    """初始化数据库（创建表）"""
    # 确保所有模型已导入
    import app.models  # noqa: F401
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

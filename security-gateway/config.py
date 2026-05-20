"""
Security Gateway 配置
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """安全网关运行时配置"""

    # 数据库
    DATABASE_URL: str = "sqlite+aiosqlite:///./security_gateway.db"

    # 引擎开关
    ENABLE_WORD_ENGINE: bool = True
    ENABLE_REGEX_ENGINE: bool = True
    ENABLE_MODEL_ENGINE: bool = False

    # 词库缓存
    WORD_ENGINE_CACHE_TTL: int = 60

    # 降级策略
    FAIL_OPEN: bool = True

    # 审计日志保留天数
    LOG_RETENTION_DAYS: int = 180

    # 服务端口
    PORT: int = 8001
    HOST: str = "0.0.0.0"

    class Config:
        env_prefix = "SG_"
        env_file = ".env"


settings = Settings()

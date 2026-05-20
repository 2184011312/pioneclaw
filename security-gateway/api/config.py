"""
配置管理 API

提供安全网关运行配置的查询和更新。
"""

from fastapi import APIRouter
from schemas.security import SecurityGatewayConfig
from config import settings

router = APIRouter(tags=["config"])


@router.get("/config", response_model=SecurityGatewayConfig)
async def get_config():
    """获取当前配置"""
    return SecurityGatewayConfig(
        enable_word_engine=settings.ENABLE_WORD_ENGINE,
        enable_regex_engine=settings.ENABLE_REGEX_ENGINE,
        enable_model_engine=settings.ENABLE_MODEL_ENGINE,
        word_engine_cache_ttl=settings.WORD_ENGINE_CACHE_TTL,
        fail_open=settings.FAIL_OPEN,
        log_retention_days=settings.LOG_RETENTION_DAYS,
    )

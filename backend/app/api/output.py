"""
多模态输出 API

提供图片生成的 REST API 端点。
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Optional
import base64

from app.core.database import get_db
from app.api.auth import get_current_active_user
from app.models import User
from app.modules.output import ImageGenerator
from app.modules.output.image_gen import ImageProvider

router = APIRouter(prefix="/output", tags=["多模态输出"])


# ------------------------------------------------------------------
# 图片生成 API
# ------------------------------------------------------------------

class ImageGenerateRequest(BaseModel):
    """图片生成请求"""
    prompt: str
    size: str = "1024x1024"
    quality: str = "standard"
    provider: str = "openai"
    model: Optional[str] = None
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    group_id: Optional[str] = None  # MiniMax 需要


class ImageGenerateResponse(BaseModel):
    """图片生成响应"""
    success: bool
    image_url: Optional[str] = None
    image_base64: Optional[str] = None
    revised_prompt: Optional[str] = None
    error: Optional[str] = None


@router.post("/image", response_model=ImageGenerateResponse)
async def generate_image(
    request: ImageGenerateRequest,
    current_user: User = Depends(get_current_active_user),
):
    """生成图片"""
    try:
        provider = ImageProvider(request.provider)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Unsupported provider: {request.provider}")

    generator = ImageGenerator(
        provider=provider,
        api_key=request.api_key,
        base_url=request.base_url,
        group_id=request.group_id,
    )

    kwargs = {}
    if request.model:
        kwargs["model"] = request.model

    result = await generator.generate(
        prompt=request.prompt,
        size=request.size,
        quality=request.quality,
        **kwargs,
    )

    return ImageGenerateResponse(
        success=result.success,
        image_url=result.image_url,
        image_base64=result.image_base64,
        revised_prompt=result.revised_prompt,
        error=result.error,
    )


@router.post("/image/download")
async def generate_and_download_image(
    request: ImageGenerateRequest,
    current_user: User = Depends(get_current_active_user),
):
    """生成图片并直接下载"""
    try:
        provider = ImageProvider(request.provider)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Unsupported provider: {request.provider}")

    generator = ImageGenerator(
        provider=provider,
        api_key=request.api_key,
        base_url=request.base_url,
        group_id=request.group_id,
    )

    result = await generator.generate(
        prompt=request.prompt,
        size=request.size,
        quality=request.quality,
    )

    if not result.success:
        raise HTTPException(status_code=500, detail=result.error)

    if result.image_base64:
        image_data = base64.b64decode(result.image_base64)
        return Response(
            content=image_data,
            media_type="image/png",
            headers={"Content-Disposition": "attachment; filename=generated_image.png"},
        )
    elif result.image_url:
        import httpx
        async with httpx.AsyncClient() as client:
            response = await client.get(result.image_url)
            if response.status_code == 200:
                return Response(
                    content=response.content,
                    media_type="image/png",
                    headers={"Content-Disposition": "attachment; filename=generated_image.png"},
                )

    raise HTTPException(status_code=500, detail="No image data available")


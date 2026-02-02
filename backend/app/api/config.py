"""
配置 API - 提供前端需要的配置信息
"""
from fastapi import APIRouter
from app.core.config import get_config

router = APIRouter(prefix="/config", tags=["config"])


@router.get("/")
def get_frontend_config():
    """获取前端配置"""
    config = get_config()

    return {
        "top_institutions": config.get("top_institutions", []),
        "subcategories": config.get("subcategories", []),
        "featured": {
            "enabled": config.get("featured", {}).get("enabled", True),
            "count": config.get("featured", {}).get("count", 5),
        }
    }

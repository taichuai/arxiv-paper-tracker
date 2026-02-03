from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
import os
from dotenv import load_dotenv

# 加载环境变量（在其他 import 之前）
load_dotenv()

from app.core.database import init_db
from app.core.config import get_config
from app.services.scheduler import scheduler
from app.api import api_router

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("../logs/app.log")
    ]
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时执行
    logger.info("=" * 50)
    logger.info("arXiv Paper Tracker 启动中...")

    # 初始化数据库
    init_db()

    # 启动调度器
    scheduler.start()

    logger.info("✓ 应用启动完成")
    logger.info("=" * 50)

    yield

    # 关闭时执行
    logger.info("应用关闭中...")
    scheduler.stop()
    logger.info("✓ 应用已关闭")


# 创建 FastAPI 应用
app = FastAPI(
    title="arXiv Paper Tracker",
    description="语音方向论文自动追踪和智能分析系统",
    version="1.0.0",
    lifespan=lifespan
)

# 配置 CORS
config = get_config()
web_config = config.get("web", {})
cors_origins = web_config.get("cors_origins", ["http://localhost:3000", "http://localhost:5173"])

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(api_router, prefix="/api")


@app.get("/")
def root():
    """根路径"""
    return {
        "message": "arXiv Paper Tracker API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
def health_check():
    """健康检查"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=web_config.get("host", "0.0.0.0"),
        port=web_config.get("port", 8000),
        reload=True
    )

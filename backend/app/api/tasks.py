from fastapi import APIRouter, BackgroundTasks
from app.services.scheduler import scheduler
from app.core.database import SessionLocal
from app.services.arxiv_fetcher import ArxivFetcher
from app.services.llm_processor import LLMProcessor
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post("/fetch-now")
def trigger_fetch(background_tasks: BackgroundTasks):
    """手动触发论文获取任务"""
    background_tasks.add_task(scheduler.run_now)
    return {"message": "论文获取任务已触发，正在后台执行"}


@router.post("/process-papers")
def trigger_process(background_tasks: BackgroundTasks, limit: int = 10):
    """手动触发 LLM 处理任务"""

    def process_task():
        db = SessionLocal()
        try:
            processor = LLMProcessor(db)
            count = processor.process_unprocessed_papers(limit=limit)
            logger.info(f"手动处理完成，处理了 {count} 篇论文")
        finally:
            db.close()

    background_tasks.add_task(process_task)
    return {"message": f"LLM 处理任务已触发，将处理最多 {limit} 篇论文"}


@router.get("/status")
def get_task_status():
    """获取调度器状态"""
    from app.core.config import get_config

    config = get_config()
    scheduler_config = config.get("scheduler", {})

    return {
        "scheduler_enabled": scheduler_config.get("enabled", True),
        "fetch_time": scheduler_config.get("fetch_time", "09:00"),
        "timezone": scheduler_config.get("timezone", "Asia/Shanghai"),
    }

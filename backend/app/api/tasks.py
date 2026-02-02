from fastapi import APIRouter, BackgroundTasks, Query
from app.services.scheduler import scheduler
from app.core.database import SessionLocal
from app.services.arxiv_fetcher import ArxivFetcher
from app.services.llm_processor import LLMProcessor
from app.services.notification import NotificationService, send_daily_notification
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post("/fetch-now")
def trigger_fetch(sync: bool = Query(default=True, description="同步执行并返回结果")):
    """手动触发论文获取任务"""
    if sync:
        # 同步执行，返回结果
        db = SessionLocal()
        try:
            fetcher = ArxivFetcher(db)
            papers = fetcher.fetch_recent_papers()
            saved_count = fetcher.save_papers(papers)

            # 同时触发 LLM 处理
            processor = LLMProcessor(db)
            processed_count = processor.process_unprocessed_papers(limit=20)

            return {
                "success": True,
                "new_papers": saved_count,
                "processed": processed_count,
                "message": f"获取完成：新增 {saved_count} 篇论文，处理了 {processed_count} 篇"
            }
        except Exception as e:
            logger.error(f"获取论文失败: {e}")
            return {
                "success": False,
                "new_papers": 0,
                "processed": 0,
                "message": f"获取失败: {str(e)}"
            }
        finally:
            db.close()
    else:
        # 异步执行（旧逻辑）
        from fastapi import BackgroundTasks
        background_tasks = BackgroundTasks()
        background_tasks.add_task(scheduler.run_now)
        return {"success": True, "message": "论文获取任务已触发，正在后台执行"}


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
    notification_config = config.get("notification", {})

    return {
        "scheduler_enabled": scheduler_config.get("enabled", True),
        "fetch_time": scheduler_config.get("fetch_time", "09:00"),
        "timezone": scheduler_config.get("timezone", "Asia/Shanghai"),
        "notification_enabled": notification_config.get("enabled", False),
        "push_time": notification_config.get("push_time", "09:30"),
    }


@router.post("/notify-now")
def trigger_notification(hours: int = Query(default=24, description="获取最近多少小时的论文")):
    """手动触发推送任务"""
    db = SessionLocal()
    try:
        service = NotificationService(db)
        papers = service.get_matching_papers(hours=hours)

        if not papers:
            return {
                "success": True,
                "message": "没有匹配的论文需要推送",
                "paper_count": 0
            }

        result = service.send_notifications(papers)
        return {
            "success": True,
            "message": f"推送完成",
            "paper_count": len(papers),
            "feishu_success": result.get("feishu", False),
            "wechat_success": result.get("wechat", False),
            "papers": [{"title": p["title"], "score": p.get("relevance_score", 0)} for p in papers]
        }
    except Exception as e:
        logger.error(f"推送失败: {e}")
        return {
            "success": False,
            "message": f"推送失败: {str(e)}",
            "paper_count": 0
        }
    finally:
        db.close()


@router.get("/notify-preview")
def preview_notification(hours: int = Query(default=24, description="获取最近多少小时的论文")):
    """预览将要推送的论文（不实际发送）"""
    db = SessionLocal()
    try:
        service = NotificationService(db)
        papers = service.get_matching_papers(hours=hours)

        return {
            "total": len(papers),
            "papers": papers
        }
    finally:
        db.close()

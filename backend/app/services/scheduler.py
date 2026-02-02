from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from app.core.database import SessionLocal
from app.core.config import get_config
from app.services.arxiv_fetcher import ArxivFetcher
from app.services.llm_processor import LLMProcessor
import logging

logger = logging.getLogger(__name__)


class PaperScheduler:
    """论文获取和处理调度器"""

    def __init__(self):
        self.config = get_config()
        self.scheduler_config = self.config.get("scheduler", {})
        self.scheduler = BackgroundScheduler()

    def start(self):
        """启动调度器"""
        if not self.scheduler_config.get("enabled", True):
            logger.info("调度器已禁用")
            return

        fetch_time = self.scheduler_config.get("fetch_time", "09:00")
        timezone = self.scheduler_config.get("timezone", "Asia/Shanghai")

        # 解析时间
        hour, minute = map(int, fetch_time.split(":"))

        # 添加定时任务
        self.scheduler.add_job(
            func=self.daily_fetch_and_process,
            trigger=CronTrigger(hour=hour, minute=minute, timezone=timezone),
            id="daily_paper_fetch",
            name="每日论文获取和处理",
            replace_existing=True,
        )

        self.scheduler.start()
        logger.info(f"✓ 调度器已启动，每天 {fetch_time} 执行任务")

    def stop(self):
        """停止调度器"""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("调度器已停止")

    def daily_fetch_and_process(self):
        """每日论文获取和处理任务"""
        logger.info("=" * 50)
        logger.info("开始执行每日论文获取任务...")

        db = SessionLocal()
        try:
            # 1. 获取论文
            fetcher = ArxivFetcher(db)
            papers = fetcher.fetch_recent_papers()

            if papers:
                saved_count = fetcher.save_papers(papers)
                logger.info(f"✓ 新增论文: {saved_count} 篇")

                # 2. 处理论文（LLM 分析）
                processor = LLMProcessor(db)
                processed_count = processor.process_unprocessed_papers(limit=saved_count)
                logger.info(f"✓ LLM 分析完成: {processed_count} 篇")
            else:
                logger.info("没有新的论文")

        except Exception as e:
            logger.error(f"每日任务执行失败: {e}", exc_info=True)
        finally:
            db.close()

        logger.info("每日论文获取任务完成")
        logger.info("=" * 50)

    def run_now(self):
        """立即执行一次任务（手动触发）"""
        logger.info("手动触发论文获取任务...")
        self.daily_fetch_and_process()


# 全局调度器实例
scheduler = PaperScheduler()

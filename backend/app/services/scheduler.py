from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from app.core.database import SessionLocal
from app.core.config import get_config
from app.services.arxiv_fetcher import ArxivFetcher
from app.services.llm_processor import LLMProcessor
from app.services.notification import send_daily_notification
from app.models import Paper, PaperAnalysis
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class PaperScheduler:
    """论文获取和处理调度器"""

    def __init__(self):
        self.config = get_config()
        self.scheduler_config = self.config.get("scheduler", {})
        self.db_config = self.config.get("database", {})
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

        # 添加每日论文获取任务
        self.scheduler.add_job(
            func=self.daily_fetch_and_process,
            trigger=CronTrigger(hour=hour, minute=minute, timezone=timezone),
            id="daily_paper_fetch",
            name="每日论文获取和处理",
            replace_existing=True,
        )

        # 添加每日推送任务（在抓取后 30 分钟执行）
        notification_config = self.config.get("notification", {})
        if notification_config.get("enabled", False):
            push_time = notification_config.get("push_time", "09:30")
            push_hour, push_minute = map(int, push_time.split(":"))
            self.scheduler.add_job(
                func=self.daily_notification,
                trigger=CronTrigger(hour=push_hour, minute=push_minute, timezone=timezone),
                id="daily_notification",
                name="每日论文推送",
                replace_existing=True,
            )
            logger.info(f"✓ 推送任务已启用，每天 {push_time} 推送")

        # 添加每周清理任务（每周日凌晨 3 点）
        self.scheduler.add_job(
            func=self.cleanup_old_papers,
            trigger=CronTrigger(day_of_week='sun', hour=3, minute=0, timezone=timezone),
            id="weekly_cleanup",
            name="每周数据清理",
            replace_existing=True,
        )

        self.scheduler.start()
        logger.info(f"✓ 调度器已启动，每天 {fetch_time} 获取论文，每周日 03:00 清理旧数据")

    def stop(self):
        """停止调度器"""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("调度器已停止")

    def cleanup_old_papers(self):
        """清理超过保留期限的旧论文"""
        retention_days = self.db_config.get("retention_days", 90)
        cutoff_date = datetime.now() - timedelta(days=retention_days)

        logger.info(f"开始清理 {retention_days} 天前的论文（截止日期: {cutoff_date.strftime('%Y-%m-%d')}）...")

        db = SessionLocal()
        try:
            # 查询要删除的论文
            old_papers = db.query(Paper).filter(Paper.published_date < cutoff_date).all()
            count = len(old_papers)

            if count > 0:
                # 删除相关的分析数据（级联删除会自动处理，但这里显式删除更安全）
                for paper in old_papers:
                    db.query(PaperAnalysis).filter(PaperAnalysis.paper_id == paper.id).delete()
                    db.delete(paper)

                db.commit()
                logger.info(f"✓ 已清理 {count} 篇旧论文")
            else:
                logger.info("没有需要清理的旧论文")

        except Exception as e:
            logger.error(f"清理旧论文失败: {e}", exc_info=True)
            db.rollback()
        finally:
            db.close()

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

                # 3. 获取处理完成后立即推送
                notification_config = self.config.get("notification", {})
                if notification_config.get("enabled", False) and processed_count > 0:
                    logger.info("获取完成，立即执行推送...")
                    result = send_daily_notification(db)
                    logger.info(f"推送结果: {result}")
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

    def daily_notification(self):
        """每日推送任务"""
        logger.info("开始执行每日推送任务...")

        db = SessionLocal()
        try:
            result = send_daily_notification(db)
            logger.info(f"推送结果: {result}")
        except Exception as e:
            logger.error(f"推送任务执行失败: {e}", exc_info=True)
        finally:
            db.close()

    def send_notification_now(self):
        """立即执行推送（手动触发）"""
        logger.info("手动触发推送任务...")
        self.daily_notification()


# 全局调度器实例
scheduler = PaperScheduler()

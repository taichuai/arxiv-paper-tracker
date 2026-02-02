import arxiv
from datetime import datetime, timedelta, timezone
from typing import List, Dict
from sqlalchemy.orm import Session
from app.models import Paper
from app.core.config import get_config
import logging

logger = logging.getLogger(__name__)


class ArxivFetcher:
    """arXiv 论文获取器"""

    def __init__(self, db: Session):
        self.db = db
        self.config = get_config()
        self.arxiv_config = self.config["arxiv"]

    def fetch_recent_papers(self) -> List[Dict]:
        """获取最近的语音相关论文（支持多天范围，自动去重）"""
        days_back = self.arxiv_config.get("days_back", 7)
        max_results = self.arxiv_config.get("max_results", 200)
        categories = self.arxiv_config.get("categories", ["cs.SD", "eess.AS"])

        # 计算日期范围（使用 UTC 时区）
        date_from = datetime.now(timezone.utc) - timedelta(days=days_back)

        # 预加载已存在的 arxiv_id（批量查询，避免 N+1）
        existing_ids = set(
            row[0] for row in self.db.query(Paper.arxiv_id).all()
        )
        logger.info(f"数据库已有 {len(existing_ids)} 篇论文")

        papers = []
        skipped_existing = 0
        skipped_date = 0
        skipped_keyword = 0

        for category in categories:
            logger.info(f"正在获取分类 {category} 的论文（最近 {days_back} 天）...")

            # 构建搜索查询
            query = f"cat:{category}"

            # 创建 arXiv 客户端
            search = arxiv.Search(
                query=query,
                max_results=max_results,
                sort_by=arxiv.SortCriterion.SubmittedDate,
                sort_order=arxiv.SortOrder.Descending
            )

            category_new = 0
            category_existing = 0

            # 获取结果
            for result in search.results():
                # 过滤日期
                if result.published < date_from:
                    skipped_date += 1
                    continue

                # 对于 cs.CL，需要额外的关键词过滤
                if category == "cs.CL" and not self._check_keywords(result):
                    skipped_keyword += 1
                    continue

                # 检查是否已存在（使用预加载的集合，O(1) 查询）
                arxiv_id = result.entry_id.split("/")[-1].split("v")[0]
                if arxiv_id in existing_ids:
                    category_existing += 1
                    skipped_existing += 1
                    continue

                paper_data = self._extract_paper_data(result)
                papers.append(paper_data)
                existing_ids.add(arxiv_id)  # 添加到集合避免重复
                category_new += 1

            logger.info(f"  {category}: 新增 {category_new} 篇, 已存在 {category_existing} 篇")

        logger.info(f"✓ 获取完成: 新论文 {len(papers)} 篇, 跳过已存在 {skipped_existing} 篇, 超出日期范围 {skipped_date} 篇")
        if skipped_keyword > 0:
            logger.info(f"  cs.CL 关键词过滤: {skipped_keyword} 篇")
        return papers

    def _check_keywords(self, result: arxiv.Result) -> bool:
        """检查论文是否包含关键词（用于 cs.CL 过滤）"""
        keywords = self.arxiv_config.get("keywords_filter", [])
        text = f"{result.title} {result.summary}".lower()

        for keyword in keywords:
            if keyword.lower() in text:
                return True
        return False

    def _paper_exists(self, arxiv_id: str) -> bool:
        """检查论文是否已存在于数据库"""
        # 清理 arxiv_id（移除版本号）
        clean_id = arxiv_id.split("/")[-1].split("v")[0]
        return self.db.query(Paper).filter(Paper.arxiv_id == clean_id).first() is not None

    def _extract_paper_data(self, result: arxiv.Result) -> Dict:
        """从 arXiv 结果中提取论文数据"""
        # 清理 arxiv_id
        arxiv_id = result.entry_id.split("/")[-1].split("v")[0]

        # 提取作者列表
        authors = [author.name for author in result.authors]

        # 提取机构信息（去重）
        affiliations = []
        seen = set()
        for author in result.authors:
            if author.affiliation and author.affiliation.strip():
                aff = author.affiliation.strip()
                if aff not in seen:
                    seen.add(aff)
                    affiliations.append(aff)

        # 提取分类
        categories = ", ".join([cat for cat in result.categories])

        return {
            "arxiv_id": arxiv_id,
            "title": result.title,
            "authors": ", ".join(authors),
            "affiliations": ", ".join(affiliations) if affiliations else None,
            "abstract": result.summary.replace("\n", " ").strip(),
            "categories": categories,
            "published_date": result.published,
            "updated_date": result.updated,
            "pdf_url": result.pdf_url,
            "arxiv_url": result.entry_id,
        }

    def save_papers(self, papers_data: List[Dict]) -> int:
        """批量保存论文到数据库"""
        if not papers_data:
            return 0

        saved_count = 0
        # 批量插入，减少 commit 次数
        for paper_data in papers_data:
            try:
                paper = Paper(**paper_data)
                self.db.add(paper)
                saved_count += 1
            except Exception as e:
                logger.error(f"添加论文失败 {paper_data['arxiv_id']}: {e}")

        try:
            self.db.commit()
            logger.info(f"✓ 成功保存 {saved_count} 篇论文到数据库")
        except Exception as e:
            logger.error(f"批量保存失败: {e}")
            self.db.rollback()
            saved_count = 0

        return saved_count

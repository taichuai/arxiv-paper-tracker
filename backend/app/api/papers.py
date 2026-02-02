from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session
from sqlalchemy import desc, func, or_
from typing import List, Optional
from datetime import datetime, timedelta
from app.core.database import get_db
from app.core.config import get_config
from app.models import Paper, PaperAnalysis
from pydantic import BaseModel


router = APIRouter(prefix="/papers", tags=["papers"])


# Pydantic 模型
class PaperResponse(BaseModel):
    id: int
    arxiv_id: str
    title: str
    authors: str
    abstract: str
    categories: str
    published_date: datetime
    pdf_url: str
    arxiv_url: str

    # 分析数据（可选）
    chinese_summary: Optional[str] = None
    keywords: Optional[List[str]] = None
    subcategory: Optional[str] = None
    relevance_score: Optional[float] = None
    affiliations: Optional[List[str]] = None
    innovation_score: Optional[float] = None
    innovation_reason: Optional[str] = None
    github_url: Optional[str] = None
    is_bookmarked: Optional[bool] = False
    is_read: Optional[bool] = False

    class Config:
        from_attributes = True


class FeaturedPaperResponse(BaseModel):
    id: int
    arxiv_id: str
    title: str
    authors: str
    published_date: datetime
    pdf_url: str
    arxiv_url: str
    chinese_summary: Optional[str] = None
    subcategory: Optional[str] = None
    affiliations: Optional[List[str]] = None
    innovation_score: Optional[float] = None
    innovation_reason: Optional[str] = None

    class Config:
        from_attributes = True


class PaperListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    papers: List[PaperResponse]


# ========== 固定路径的路由必须放在动态路径之前 ==========

@router.get("/", response_model=PaperListResponse)
def get_papers(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort_by: str = Query("date_desc", regex="^(date_desc|date_asc|relevance)$"),
    subcategory: Optional[str] = None,
    bookmarked_only: bool = False,
    days: Optional[int] = Query(None, ge=1, le=365),
    db: Session = Depends(get_db)
):
    """获取论文列表"""

    # 构建查询
    query = db.query(Paper, PaperAnalysis).outerjoin(
        PaperAnalysis, Paper.id == PaperAnalysis.paper_id
    )

    # 过滤条件
    if subcategory:
        query = query.filter(PaperAnalysis.subcategory == subcategory)

    if bookmarked_only:
        query = query.filter(PaperAnalysis.is_bookmarked == True)

    if days:
        date_from = datetime.now() - timedelta(days=days)
        query = query.filter(Paper.published_date >= date_from)

    # 排序
    if sort_by == "date_desc":
        query = query.order_by(desc(Paper.published_date))
    elif sort_by == "date_asc":
        query = query.order_by(Paper.published_date)
    elif sort_by == "relevance":
        query = query.order_by(desc(PaperAnalysis.relevance_score))

    # 分页
    total = query.count()
    offset = (page - 1) * page_size
    results = query.offset(offset).limit(page_size).all()

    # 构建响应（列表页不返回完整 abstract，节省传输）
    papers = []
    for paper, analysis in results:
        paper_dict = {
            "id": paper.id,
            "arxiv_id": paper.arxiv_id,
            "title": paper.title,
            "authors": paper.authors,
            "abstract": paper.abstract[:200] + "..." if len(paper.abstract) > 200 else paper.abstract,
            "categories": paper.categories,
            "published_date": paper.published_date,
            "pdf_url": paper.pdf_url,
            "arxiv_url": paper.arxiv_url,
        }

        if analysis:
            paper_dict.update({
                "chinese_summary": analysis.chinese_summary,
                "keywords": analysis.keywords,
                "subcategory": analysis.subcategory,
                "relevance_score": analysis.relevance_score,
                "affiliations": analysis.affiliations,
                "innovation_score": analysis.innovation_score,
                "innovation_reason": analysis.innovation_reason,
                "github_url": analysis.github_url,
                "is_bookmarked": analysis.is_bookmarked,
                "is_read": analysis.is_read,
            })

        papers.append(PaperResponse(**paper_dict))

    return PaperListResponse(
        total=total,
        page=page,
        page_size=page_size,
        papers=papers
    )


@router.get("/search", response_model=PaperListResponse)
def search_papers(
    q: Optional[str] = Query(None, description="搜索关键词（标题、摘要、作者）"),
    subcategory: Optional[str] = Query(None, description="子领域分类"),
    institution: Optional[str] = Query(None, description="机构关键词"),
    min_score: Optional[float] = Query(None, ge=0, le=10, description="最低相关性评分"),
    max_score: Optional[float] = Query(None, ge=0, le=10, description="最高相关性评分"),
    date_from: Optional[str] = Query(None, description="开始日期 YYYY-MM-DD"),
    date_to: Optional[str] = Query(None, description="结束日期 YYYY-MM-DD"),
    has_github: Optional[bool] = Query(None, description="是否有 GitHub 链接"),
    bookmarked_only: bool = Query(False, description="仅显示收藏"),
    sort_by: str = Query("date_desc", regex="^(date_desc|date_asc|relevance|innovation)$"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """高级搜索论文"""

    # 构建查询
    query = db.query(Paper, PaperAnalysis).outerjoin(
        PaperAnalysis, Paper.id == PaperAnalysis.paper_id
    )

    # 全文搜索（标题、摘要、作者）
    if q:
        search_term = f"%{q}%"
        query = query.filter(
            or_(
                Paper.title.ilike(search_term),
                Paper.abstract.ilike(search_term),
                Paper.authors.ilike(search_term),
                PaperAnalysis.chinese_summary.ilike(search_term)
            )
        )

    # 子领域筛选
    if subcategory:
        query = query.filter(PaperAnalysis.subcategory == subcategory)

    # 机构筛选
    if institution:
        # 使用 JSON 字段搜索（SQLite 中 affiliations 是 JSON 数组）
        query = query.filter(
            func.json_extract(PaperAnalysis.affiliations, '$').like(f'%{institution}%')
        )

    # 评分范围
    if min_score is not None:
        query = query.filter(PaperAnalysis.relevance_score >= min_score)
    if max_score is not None:
        query = query.filter(PaperAnalysis.relevance_score <= max_score)

    # 日期范围
    if date_from:
        try:
            from_date_parsed = datetime.strptime(date_from, "%Y-%m-%d")
            query = query.filter(Paper.published_date >= from_date_parsed)
        except ValueError:
            pass
    if date_to:
        try:
            to_date_parsed = datetime.strptime(date_to, "%Y-%m-%d") + timedelta(days=1)
            query = query.filter(Paper.published_date < to_date_parsed)
        except ValueError:
            pass

    # GitHub 链接筛选
    if has_github is True:
        query = query.filter(PaperAnalysis.github_url.isnot(None))
    elif has_github is False:
        query = query.filter(PaperAnalysis.github_url.is_(None))

    # 收藏筛选
    if bookmarked_only:
        query = query.filter(PaperAnalysis.is_bookmarked == True)

    # 排序
    if sort_by == "date_desc":
        query = query.order_by(desc(Paper.published_date))
    elif sort_by == "date_asc":
        query = query.order_by(Paper.published_date)
    elif sort_by == "relevance":
        query = query.order_by(desc(PaperAnalysis.relevance_score))
    elif sort_by == "innovation":
        query = query.order_by(desc(PaperAnalysis.innovation_score))

    # 分页
    total = query.count()
    offset = (page - 1) * page_size
    results = query.offset(offset).limit(page_size).all()

    # 构建响应（列表页不返回完整 abstract）
    papers = []
    for paper, analysis in results:
        paper_dict = {
            "id": paper.id,
            "arxiv_id": paper.arxiv_id,
            "title": paper.title,
            "authors": paper.authors,
            "abstract": paper.abstract[:200] + "..." if len(paper.abstract) > 200 else paper.abstract,
            "categories": paper.categories,
            "published_date": paper.published_date,
            "pdf_url": paper.pdf_url,
            "arxiv_url": paper.arxiv_url,
        }

        if analysis:
            paper_dict.update({
                "chinese_summary": analysis.chinese_summary,
                "keywords": analysis.keywords,
                "subcategory": analysis.subcategory,
                "relevance_score": analysis.relevance_score,
                "affiliations": analysis.affiliations,
                "innovation_score": analysis.innovation_score,
                "innovation_reason": analysis.innovation_reason,
                "github_url": analysis.github_url,
                "is_bookmarked": analysis.is_bookmarked,
                "is_read": analysis.is_read,
            })

        papers.append(PaperResponse(**paper_dict))

    return PaperListResponse(
        total=total,
        page=page,
        page_size=page_size,
        papers=papers
    )


@router.get("/stats/summary")
def get_stats(db: Session = Depends(get_db)):
    """获取统计信息"""
    total_papers = db.query(func.count(Paper.id)).scalar()
    total_bookmarked = db.query(func.count(PaperAnalysis.id)).filter(
        PaperAnalysis.is_bookmarked == True
    ).scalar()

    # 按子领域统计
    subcategory_stats = db.query(
        PaperAnalysis.subcategory,
        func.count(PaperAnalysis.id)
    ).group_by(PaperAnalysis.subcategory).all()

    # 最近7天论文数
    date_7days_ago = datetime.now() - timedelta(days=7)
    recent_papers = db.query(func.count(Paper.id)).filter(
        Paper.published_date >= date_7days_ago
    ).scalar()

    return {
        "total_papers": total_papers,
        "total_bookmarked": total_bookmarked,
        "recent_papers": recent_papers,
        "subcategory_distribution": {cat: count for cat, count in subcategory_stats}
    }


@router.get("/featured/weekly", response_model=List[FeaturedPaperResponse])
def get_featured_papers(db: Session = Depends(get_db)):
    """获取本周精选论文 - 优先从头部机构中选取"""
    config = get_config()
    featured_config = config.get("featured", {})

    if not featured_config.get("enabled", True):
        return []

    count = featured_config.get("count", 5)
    min_score = featured_config.get("min_score", 6.0)
    target_subcategories = featured_config.get("target_subcategories", [])

    # 从配置读取头部机构列表
    top_institutions = config.get("top_institutions", [])

    # 获取最近 7 天的论文
    date_7days_ago = datetime.now() - timedelta(days=7)

    # 查询所有有分析的论文
    query = (
        db.query(Paper, PaperAnalysis)
        .join(PaperAnalysis, Paper.id == PaperAnalysis.paper_id)
        .filter(Paper.published_date >= date_7days_ago)
    )

    # 如果配置了目标子领域，筛选
    if target_subcategories:
        query = query.filter(PaperAnalysis.subcategory.in_(target_subcategories))

    all_papers = query.all()

    # 筛选头部机构的论文
    top_inst_papers = []
    other_papers = []

    for paper, analysis in all_papers:
        affiliations = analysis.affiliations or []
        is_top = False
        for aff in affiliations:
            if aff and any(inst.lower() in aff.lower() for inst in top_institutions):
                is_top = True
                break

        score = analysis.innovation_score or analysis.relevance_score or 0
        if score >= min_score:
            if is_top:
                top_inst_papers.append((paper, analysis, score))
            else:
                other_papers.append((paper, analysis, score))

    # 按分数排序
    top_inst_papers.sort(key=lambda x: x[2], reverse=True)
    other_papers.sort(key=lambda x: x[2], reverse=True)

    # 优先选头部机构论文，不够再补充其他
    selected = top_inst_papers[:count]
    if len(selected) < count:
        selected.extend(other_papers[:count - len(selected)])

    # 构建响应
    featured_papers = []
    for paper, analysis, score in selected:
        featured_papers.append(FeaturedPaperResponse(
            id=paper.id,
            arxiv_id=paper.arxiv_id,
            title=paper.title,
            authors=paper.authors,
            published_date=paper.published_date,
            pdf_url=paper.pdf_url,
            arxiv_url=paper.arxiv_url,
            chinese_summary=analysis.chinese_summary,
            subcategory=analysis.subcategory,
            affiliations=analysis.affiliations,
            innovation_score=analysis.innovation_score,
            innovation_reason=analysis.innovation_reason,
        ))

    return featured_papers


@router.get("/export/bibtex", response_class=PlainTextResponse)
def export_bibtex(
    ids: Optional[str] = Query(None, description="论文 ID 列表，逗号分隔"),
    bookmarked_only: bool = Query(False, description="仅导出收藏"),
    db: Session = Depends(get_db)
):
    """批量导出 BibTeX"""
    if ids:
        # 导出指定论文
        paper_ids = [int(i.strip()) for i in ids.split(",") if i.strip().isdigit()]
        papers = db.query(Paper).filter(Paper.id.in_(paper_ids)).all()
    elif bookmarked_only:
        # 导出所有收藏
        papers = (
            db.query(Paper)
            .join(PaperAnalysis, Paper.id == PaperAnalysis.paper_id)
            .filter(PaperAnalysis.is_bookmarked == True)
            .all()
        )
    else:
        raise HTTPException(status_code=400, detail="请提供论文 ID 或选择仅导出收藏")

    if not papers:
        raise HTTPException(status_code=404, detail="没有找到论文")

    bibtex_entries = [_generate_bibtex(paper) for paper in papers]
    return "\n\n".join(bibtex_entries)


# ========== 动态路径的路由放在后面 ==========

@router.get("/{paper_id}", response_model=PaperResponse)
def get_paper(paper_id: int, db: Session = Depends(get_db)):
    """获取单篇论文详情"""
    paper = db.query(Paper).filter(Paper.id == paper_id).first()
    if not paper:
        raise HTTPException(status_code=404, detail="论文不存在")

    analysis = db.query(PaperAnalysis).filter(PaperAnalysis.paper_id == paper_id).first()

    paper_dict = {
        "id": paper.id,
        "arxiv_id": paper.arxiv_id,
        "title": paper.title,
        "authors": paper.authors,
        "abstract": paper.abstract,
        "categories": paper.categories,
        "published_date": paper.published_date,
        "pdf_url": paper.pdf_url,
        "arxiv_url": paper.arxiv_url,
    }

    if analysis:
        paper_dict.update({
            "chinese_summary": analysis.chinese_summary,
            "keywords": analysis.keywords,
            "subcategory": analysis.subcategory,
            "relevance_score": analysis.relevance_score,
            "affiliations": analysis.affiliations,
            "innovation_score": analysis.innovation_score,
            "innovation_reason": analysis.innovation_reason,
            "github_url": analysis.github_url,
            "is_bookmarked": analysis.is_bookmarked,
            "is_read": analysis.is_read,
        })

    return PaperResponse(**paper_dict)


@router.get("/{paper_id}/bibtex", response_class=PlainTextResponse)
def get_paper_bibtex(paper_id: int, db: Session = Depends(get_db)):
    """获取单篇论文的 BibTeX"""
    paper = db.query(Paper).filter(Paper.id == paper_id).first()
    if not paper:
        raise HTTPException(status_code=404, detail="论文不存在")

    return _generate_bibtex(paper)


@router.post("/{paper_id}/bookmark")
def toggle_bookmark(paper_id: int, db: Session = Depends(get_db)):
    """切换收藏状态"""
    analysis = db.query(PaperAnalysis).filter(PaperAnalysis.paper_id == paper_id).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="论文分析不存在")

    analysis.is_bookmarked = not analysis.is_bookmarked
    db.commit()

    return {"bookmarked": analysis.is_bookmarked}


@router.post("/{paper_id}/read")
def mark_as_read(paper_id: int, db: Session = Depends(get_db)):
    """标记为已读"""
    analysis = db.query(PaperAnalysis).filter(PaperAnalysis.paper_id == paper_id).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="论文分析不存在")

    analysis.is_read = True
    db.commit()

    return {"success": True}


# ========== 辅助函数 ==========

def _generate_bibtex(paper: Paper) -> str:
    """生成单篇论文的 BibTeX"""
    # 清理作者格式
    authors = paper.authors.replace(", ", " and ")

    # 生成 cite key: 第一作者姓 + 年份 + 标题首词
    first_author = paper.authors.split(",")[0].split()[-1] if paper.authors else "Unknown"
    year = paper.published_date.year if paper.published_date else "2024"
    title_word = paper.title.split()[0] if paper.title else "paper"
    cite_key = f"{first_author}{year}{title_word}".lower()
    # 移除特殊字符
    cite_key = ''.join(c for c in cite_key if c.isalnum())

    bibtex = f"""@article{{{cite_key},
  title={{{paper.title}}},
  author={{{authors}}},
  journal={{arXiv preprint arXiv:{paper.arxiv_id}}},
  year={{{year}}},
  url={{{paper.arxiv_url}}},
  eprint={{{paper.arxiv_id}}},
  archivePrefix={{arXiv}},
  primaryClass={{{paper.categories.split(',')[0] if paper.categories else 'cs.SD'}}}
}}"""
    return bibtex

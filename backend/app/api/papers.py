from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from typing import List, Optional
from datetime import datetime, timedelta
from app.core.database import get_db
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
    is_bookmarked: Optional[bool] = False
    is_read: Optional[bool] = False

    class Config:
        from_attributes = True


class PaperListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    papers: List[PaperResponse]


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

    # 构建响应
    papers = []
    for paper, analysis in results:
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
            "is_bookmarked": analysis.is_bookmarked,
            "is_read": analysis.is_read,
        })

    return PaperResponse(**paper_dict)


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

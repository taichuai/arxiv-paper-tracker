from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Float, ForeignKey, JSON, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Paper(Base):
    """论文基础信息表"""
    __tablename__ = "papers"

    id = Column(Integer, primary_key=True, index=True)
    arxiv_id = Column(String(50), unique=True, index=True, nullable=False)
    title = Column(String(500), nullable=False)
    authors = Column(Text, nullable=False)  # JSON string of author list
    abstract = Column(Text, nullable=False)
    categories = Column(String(200), nullable=False)  # Comma-separated
    published_date = Column(DateTime, nullable=False, index=True)
    updated_date = Column(DateTime, nullable=True)
    pdf_url = Column(String(200), nullable=False)
    arxiv_url = Column(String(200), nullable=False)

    # 元数据
    created_at = Column(DateTime, default=datetime.utcnow)

    # 关系
    analysis = relationship("PaperAnalysis", back_populates="paper", uselist=False, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Paper(arxiv_id='{self.arxiv_id}', title='{self.title[:50]}...')>"


class PaperAnalysis(Base):
    """论文 LLM 分析结果表"""
    __tablename__ = "paper_analysis"

    id = Column(Integer, primary_key=True, index=True)
    paper_id = Column(Integer, ForeignKey("papers.id"), unique=True, nullable=False)

    # LLM 生成的内容
    chinese_summary = Column(Text, nullable=True)  # 中文摘要
    keywords = Column(JSON, nullable=True)  # List of keywords
    subcategory = Column(String(50), nullable=True, index=True)  # 子领域分类
    relevance_score = Column(Float, nullable=True, index=True)  # 相关性评分 0-10

    # 用户交互
    is_bookmarked = Column(Boolean, default=False, index=True)
    is_read = Column(Boolean, default=False)
    user_notes = Column(Text, nullable=True)

    # 元数据
    processed_at = Column(DateTime, default=datetime.utcnow)

    # 关系
    paper = relationship("Paper", back_populates="analysis")

    def __repr__(self):
        return f"<PaperAnalysis(paper_id={self.paper_id}, subcategory='{self.subcategory}', score={self.relevance_score})>"


class UserPreference(Base):
    """用户偏好设置表（单记录）"""
    __tablename__ = "user_preferences"

    id = Column(Integer, primary_key=True)

    # 研究兴趣关键词
    research_interests = Column(JSON, nullable=True)  # Dict with primary/secondary/tertiary
    excluded_keywords = Column(JSON, nullable=True)  # List of keywords to exclude

    # 显示设置
    default_sort = Column(String(20), default="date_desc")  # date_desc, relevance, date_asc
    papers_per_page = Column(Integer, default=20)

    # 更新时间
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<UserPreference(id={self.id})>"

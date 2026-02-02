from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from pathlib import Path
from app.models.paper import Base
from app.core.config import settings


# 确保数据目录存在
data_dir = Path(__file__).parent.parent.parent.parent / "data"
data_dir.mkdir(exist_ok=True)

# 创建数据库引擎
db_path = data_dir / "papers.db"
SQLALCHEMY_DATABASE_URL = f"sqlite:///{db_path}"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},  # SQLite 需要
    echo=False  # 设置为 True 可以看到 SQL 语句
)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """初始化数据库，创建所有表"""
    Base.metadata.create_all(bind=engine)
    print(f"✓ 数据库初始化完成: {db_path}")


def get_db():
    """FastAPI 依赖注入函数"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

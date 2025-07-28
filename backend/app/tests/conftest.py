import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.database import Base
from app.models import AnalysisRecord  # 確保模型被導入


# 使用 SQLite 記憶體資料庫進行測試
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db():
    """建立測試用資料庫session"""
    # 建立所有表格
    Base.metadata.create_all(bind=engine)
    
    # 建立session
    session = TestingSessionLocal()
    
    try:
        yield session
    finally:
        session.close()
        # 清理測試資料
        Base.metadata.drop_all(bind=engine)
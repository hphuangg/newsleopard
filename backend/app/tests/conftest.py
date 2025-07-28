import pytest
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# 建立測試專用的 Base，避免依賴複雜的配置
Base = declarative_base()

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
    # 修改模型的 Base 為測試用的 Base
    import app.models.analysis
    original_base = app.models.analysis.Base
    app.models.analysis.Base = Base
    
    # 重新定義模型使用測試 Base
    from app.models.analysis import AnalysisRecord
    AnalysisRecord.__table__.metadata = Base.metadata
    
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
        # 恢復原始 Base
        app.models.analysis.Base = original_base
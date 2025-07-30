"""
共用資料庫連接管理

提供 Backend 和 Worker 共用的資料庫連接。
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from shared.config.settings import settings

# 建立資料庫引擎
engine = create_engine(settings.database.url)

# 建立 Session 工廠
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 建立 Base 類別
Base = declarative_base()


def get_db():
    """取得資料庫 Session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
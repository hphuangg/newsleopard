"""
Backend 資料庫連接

使用 shared 模組的資料庫配置。
"""

import sys
from pathlib import Path

# 添加 shared 模組到路徑
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "shared"))

from shared.db.database import Base, engine, SessionLocal, get_db

# 重新匯出供 Backend 使用
__all__ = ["Base", "engine", "SessionLocal", "get_db"]
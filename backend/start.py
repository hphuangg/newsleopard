#!/usr/bin/env python3
"""
Backend 服務啟動腳本

設定正確的 Python 路徑後啟動 FastAPI 應用程式。
"""

import sys
import os
from pathlib import Path

# 設定項目根目錄
PROJECT_ROOT = Path(__file__).parent.parent
BACKEND_ROOT = Path(__file__).parent

# 添加必要的路徑
sys.path.insert(0, str(PROJECT_ROOT / "shared"))
sys.path.insert(0, str(BACKEND_ROOT))

# 設定環境變數
os.environ.setdefault("PYTHONPATH", f"{PROJECT_ROOT / 'shared'}:{BACKEND_ROOT}")

if __name__ == "__main__":
    import uvicorn
    
    # 啟動 FastAPI 應用程式
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_dirs=[str(BACKEND_ROOT), str(PROJECT_ROOT / "shared")]
    )
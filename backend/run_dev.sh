#!/bin/bash
# Backend 開發環境啟動腳本

# 設定 Python 路徑
export PYTHONPATH="/Users/hphuang/IdeaProjects/newsleopard/shared:/Users/hphuang/IdeaProjects/newsleopard/backend:$PYTHONPATH"

# 切換到 backend 目錄
cd "$(dirname "$0")"

# 啟動 FastAPI
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
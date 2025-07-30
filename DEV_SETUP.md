# 🚀 開發環境設置指南

## 📋 重構後的新架構

```
newsleopard/
├── backend/              # FastAPI API 服務
├── worker/               # 獨立 Worker 服務
├── shared/               # 共用模組
└── docker-compose.yml    # 統一編排
```

## 💻 VSCode 開發設置

### 1. 使用 VSCode Debug 配置 (推薦)

已建立 `.vscode/launch.json` 配置：

- **Backend FastAPI** - 啟動 API 服務
- **Worker Service** - 啟動 Worker 服務

使用方式：
1. 按 `F5` 或到 Debug 面板
2. 選擇 "Backend FastAPI" 
3. 點擊開始調試

### 2. 終端啟動方式

#### Backend 服務
```bash
# 設定環境變數
export PYTHONPATH="/Users/hphuang/IdeaProjects/newsleopard/shared:/Users/hphuang/IdeaProjects/newsleopard/backend:$PYTHONPATH"

# 啟動 Backend
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

#### Worker 服務
```bash
# 設定環境變數
export PYTHONPATH="/Users/hphuang/IdeaProjects/newsleopard/shared:/Users/hphuang/IdeaProjects/newsleopard/worker:$PYTHONPATH"

# 啟動 Worker
python worker/app/worker.py
```

### 3. Docker 方式 (完整環境)

```bash
# 啟動所有服務 (Postgres + LocalStack + Backend + Worker)
docker-compose up

# 只啟動依賴服務
docker-compose up postgres localstack
```

## 🔧 環境變數設置

需要設置的環境變數 (或在 `.env` 檔案中)：

```bash
# 資料庫
POSTGRES_SERVER=localhost
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=backend

# AWS/SQS (LocalStack)
AWS_ACCESS_KEY_ID=test
AWS_SECRET_ACCESS_KEY=test
AWS_REGION=us-east-1
AWS_SQS_ENDPOINT_URL=http://localhost:4566

# SQS 佇列 URLs
SQS_SEND_QUEUE_URL=http://sqs.us-east-1.localhost.localstack.cloud:4566/000000000000/send-queue
SQS_BATCH_QUEUE_URL=http://sqs.us-east-1.localhost.localstack.cloud:4566/000000000000/batch-queue
SQS_SEND_DLQ_URL=http://sqs.us-east-1.localhost.localstack.cloud:4566/000000000000/send-dlq
SQS_BATCH_DLQ_URL=http://sqs.us-east-1.localhost.localstack.cloud:4566/000000000000/batch-dlq
```

## ✅ 驗證設置

### 測試 Backend
```bash
curl http://localhost:8000/health
# 應回傳: {"status": "healthy"}
```

### 測試 API
```bash
curl -X POST http://localhost:8000/api/v1/send/send-message \
  -H "Content-Type: application/json" \
  -d '{"content":"Hello","channel":"line","recipients":[{"id":"user1","type":"line"}]}'
```

## 🐛 常見問題

### 1. ModuleNotFoundError: No module named 'shared'
**解決方案**: 確保設定了正確的 PYTHONPATH
```bash
export PYTHONPATH="/Users/hphuang/IdeaProjects/newsleopard/shared:/Users/hphuang/IdeaProjects/newsleopard/backend:$PYTHONPATH"
```

### 2. pydantic.errors.PydanticImportError
**解決方案**: 確保安裝了 pydantic-settings
```bash
pip install pydantic-settings
```

### 3. Database connection errors
**解決方案**: 確保設定了資料庫環境變數或啟動了 Docker Postgres

## 📚 重構說明

TASK-13 完成的重構：
- ✅ **組件分離**: Backend 和 Worker 完全解耦
- ✅ **共用模組**: 配置、模型、Schema 統一管理
- ✅ **Docker 支援**: 多容器獨立部署
- ✅ **開發友善**: VSCode 配置完整

下一步建議：**TASK-04 發送管道抽象層**，現在可以專注在 Worker 端實作！
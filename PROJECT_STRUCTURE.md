# 專案結構說明

## 概述
Line 文案 AI 分析工具 - 提供文案評分分析與試寄功能

## 目錄結構

```
newsleopard/
├── backend/                    # FastAPI 後端應用
│   ├── app/
│   │   ├── api/v1/            # API 路由
│   │   │   └── endpoints/     # API 端點實現 (analysis.py, send.py, items.py)
│   │   ├── core/              # 核心配置
│   │   │   ├── config.py      # 主要配置
│   │   │   ├── sqs_config.py  # SQS 配置
│   │   │   ├── dependencies.py
│   │   │   ├── error_handlers.py
│   │   │   └── exceptions.py
│   │   ├── crud/              # 資料庫操作層
│   │   │   ├── analysis.py
│   │   │   ├── batch_send_record.py
│   │   │   └── message_send_record.py
│   │   ├── db/                # 資料庫連接
│   │   ├── models/            # SQLAlchemy 資料庫模型
│   │   │   ├── analysis.py
│   │   │   ├── batch_send_record.py  
│   │   │   └── message_send_record.py
│   │   ├── schemas/           # Pydantic 模型
│   │   │   ├── analysis.py
│   │   │   └── send.py
│   │   ├── services/          # 業務邏輯服務
│   │   │   ├── ai_client/     # AI 客戶端抽象層
│   │   │   │   ├── base.py
│   │   │   │   ├── claude_client.py
│   │   │   │   ├── openai_client.py
│   │   │   │   └── factory.py
│   │   │   ├── prompts/       # AI 提示詞管理
│   │   │   │   ├── registry.py
│   │   │   │   └── templates.py
│   │   │   ├── analysis_service.py
│   │   │   ├── send_service.py
│   │   │   └── sqs_queue_manager.py
│   │   ├── workers/           # SQS 背景工作程序
│   │   │   └── sqs_worker.py
│   │   └── tests/             # 測試檔案
│   ├── alembic/               # 資料庫遷移
│   │   └── versions/          # 遷移版本
│   ├── shared/                # 共享元件 (準備移至根目錄)
│   └── worker/                # Worker 應用程式 (準備移至根目錄)
├── worker/                    # 獨立 Worker 服務
│   └── app/
│       ├── channels/          # 發送管道抽象層
│       │   ├── factory.py     # 管道工廠
│       │   ├── line_bot.py    # Line Bot 整合
│       │   └── manager.py     # 管道管理器
│       ├── handlers/          # 訊息處理器
│       │   └── message_handler.py
│       └── worker.py          # 主要 Worker 邏輯
├── shared/                    # 共享元件庫
│   ├── channels/              # 發送管道基礎類別
│   │   ├── base.py
│   │   └── exceptions.py
│   ├── config/                # 共享配置
│   │   └── settings.py
│   ├── db/                    # 共享資料庫連接
│   │   └── database.py
│   ├── models/                # 共享資料模型
│   │   ├── batch_send_record.py
│   │   └── message_send_record.py
│   ├── schemas/               # 共享 Pydantic 模型
│   │   └── send.py
│   └── utils/                 # 共享工具
│       ├── sqs_client.py
│       └── sqs_config.py
├── devtools/                  # 開發工具
│   └── sqs_monitor.py         # SQS 監控工具
├── docs/                      # 設計文件
│   ├── API.md                 # ✅ API 設計規格
│   ├── DATABASE.md            # ✅ 資料庫設計規格
│   └── PERFORMANCE.md         # 效能相關文件
├── volume/                    # Docker 掛載卷
│   ├── cache/                 # 暫存檔案
│   ├── logs/                  # 日誌檔案
│   └── tmp/                   # 臨時檔案
└── prompts/                   # 開發流程模板
    ├── generate_tasks.md
    ├── generate_user_stories.md
    └── process_tasks.md       # 任務執行流程
```

## 已完成功能

### ✅ US-01: 文案分析與建議系統
- **API與Schema設計**: 完整的 API 設計規格與資料庫設計
- **AI 客戶端抽象層**: 支援 Claude 和 OpenAI 的可擴展架構
- **文案分析服務**: 完整的文案評分與建議功能
- **資料庫模型**: Analysis 記錄的完整 CRUD 操作

### ✅ US-02: 非同步訊息佇列系統
- **AWS SQS 整合**: 完整的 SQS 佇列管理與訊息處理
- **Worker 服務**: 獨立的背景工作程序，處理訊息傳送任務
- **發送管道抽象層**: 可擴展的訊息發送架構
- **Line Bot 整合**: Line 訊息發送功能實作
- **批次發送記錄**: 完整的發送記錄追蹤系統

### 🔧 開發工具與基礎建設
- **Docker 化部署**: 完整的 Docker 容器化環境
- **資料庫遷移**: Alembic 遷移管理
- **開發監控工具**: SQS 監控工具 (`devtools/sqs_monitor.py`)
- **共享元件庫**: 模組化的共享元件架構
- **測試覆蓋**: 全面的單元測試與整合測試

## 快速定位文件

### API 相關
- API 設計規格: `docs/API.md`
- 資料庫設計: `docs/DATABASE.md`
- 效能文件: `docs/PERFORMANCE.md`
- 後端程式碼: `backend/app/`

### 核心服務
- 文案分析: `backend/app/services/analysis_service.py`
- 訊息發送: `backend/app/services/send_service.py`
- AI 客戶端: `backend/app/services/ai_client/`
- SQS 管理: `backend/app/services/sqs_queue_manager.py`

### Worker 與佇列
- Worker 主程式: `worker/app/worker.py`
- 訊息處理器: `worker/app/handlers/message_handler.py`
- 發送管道: `worker/app/channels/`
- SQS Worker: `backend/app/workers/sqs_worker.py`

### 共享元件
- 共享配置: `shared/config/settings.py`
- 共享模型: `shared/models/`
- 共享工具: `shared/utils/`
- 發送管道基礎: `shared/channels/`

### 開發工具
- SQS 監控: `devtools/sqs_monitor.py`
- 開發設定: `DEV_SETUP.md`
- SQS 設定文件: `backend/SQS_SETUP.md`, `backend/SQS_LOCAL_DEV.md`

### 設定檔
- 主要配置: `backend/app/core/config.py`
- SQS 配置: `backend/app/core/sqs_config.py`
- Docker 設定: `backend/docker-compose.yml`, `docker-compose.yml`
- 依賴管理: `backend/requirements.txt`, `backend/pyproject.toml`
- Worker 依賴: `worker/requirements.txt`

## 系統架構

### 微服務架構
- **Backend API**: FastAPI 後端服務，提供 REST API
- **Worker Service**: 獨立的訊息處理服務
- **Shared Library**: 共享元件庫，避免程式碼重複

### 訊息佇列架構
- **AWS SQS**: 非同步訊息佇列
- **發送管道抽象層**: 支援多種發送管道 (Line Bot, Email 等)
- **批次處理**: 支援大量訊息的批次發送

### 資料庫設計
- **PostgreSQL**: 主要資料庫
- **Alembic**: 資料庫版本管理
- **分析記錄**: 文案分析結果儲存
- **發送記錄**: 訊息發送狀態追蹤

## 開發工作流程

1. **環境設定**: 參考 `DEV_SETUP.md`
2. **任務規劃**: 參考 `prompts/generate_user_stories.md`
3. **任務分解**: 參考 `prompts/generate_tasks.md`
4. **任務執行**: 參考 `prompts/process_tasks.md`
5. **API 設計**: 更新 `docs/API.md`
6. **資料庫設計**: 更新 `docs/DATABASE.md`
7. **程式實作**: 在對應的服務目錄中實作
8. **測試**: 新增單元測試與整合測試
9. **部署**: 使用 Docker 容器化部署

## 服務啟動順序

1. **資料庫**: `docker-compose up postgres`
2. **LocalStack** (開發環境): `docker-compose up localstack`
3. **Backend API**: `cd backend && python start.py`
4. **Worker Service**: `cd worker && python -m app.worker`
5. **SQS 監控** (可選): `python devtools/sqs_monitor.py`

## 分支命名規範

- Feature 分支: `feature/{user_story_id}-{task_id}-{簡短名稱}`
- 例如: `feature/US-02-TASK-04-Line-Bot-Integration`
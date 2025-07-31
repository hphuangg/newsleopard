# 專案結構說明

## 概述
Line 文案 AI 分析工具 - 提供文案評分分析與試寄功能

## 目錄結構

```
newsleopard/
├── backend/                    # FastAPI 後端應用
│   ├── app/
│   │   ├── api/v1/            # API 路由
│   │   │   └── endpoints/     # API 端點實現
│   │   ├── core/              # 核心配置
│   │   ├── crud/              # 資料庫操作層
│   │   ├── db/                # 資料庫連接
│   │   ├── models/            # 資料庫模型
│   │   ├── schemas/           # Pydantic 模型
│   │   └── tests/             # 測試檔案
│   └── README.md              # 後端說明文件
├── docs/                      # 設計文件
│   ├── API.md                 # ✅ API 設計規格
│   └── DATABASE.md            # ✅ 資料庫設計規格
├── .sprints/                  # Sprint 管理
│   └── sprint1/
│       └── [US-01]-文案分析與建議/
│           └── [US-01][TASK-03][後端][TODO]API與Schema設計.md  # ✅ 已完成
└── prompts/                   # 開發流程模板
    ├── generate_tasks.md
    ├── generate_user_stories.md
    └── process_tasks.md       # 任務執行流程
```

## 已完成功能

### ✅ US-01 TASK-03: API與Schema設計
- **狀態**: COMPLETED
- **產出檔案**:
  - `docs/API.md` - 完整 API 設計規格
  - `docs/DATABASE.md` - 完整資料庫設計規格
- **功能**: POST /api/v1/analyze 文案分析 API 設計

## 快速定位文件

### API 相關
- API 設計規格: `docs/API.md`
- 資料庫設計: `docs/DATABASE.md`
- 後端程式碼: `backend/app/`

### 任務管理
- Sprint 任務: `.sprints/sprint1/[US-01]-文案分析與建議/`
- 開發流程: `prompts/process_tasks.md`
- 任務生成: `prompts/generate_tasks.md`

### 設定檔
- 後端設定: `backend/app/core/config.py`
- Docker 設定: `backend/docker-compose.yml`
- 依賴管理: `backend/requirements.txt`

## 開發工作流程

1. **任務規劃**: 參考 `prompts/generate_user_stories.md`
2. **任務分解**: 參考 `prompts/generate_tasks.md`
3. **任務執行**: 參考 `prompts/process_tasks.md`
4. **API 設計**: 更新 `docs/API.md`
5. **資料庫設計**: 更新 `docs/DATABASE.md`
6. **程式實作**: 在 `backend/app/` 中實作
7. **測試**: 在 `backend/app/tests/` 中新增測試

## 分支命名規範

- Feature 分支: `feature/{user_story_id}-{task_id}-{簡短名稱}`
- 例如: `feature/US-01-TASK-03-API-Schema-Design`
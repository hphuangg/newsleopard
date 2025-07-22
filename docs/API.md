# Line 文案分析 API 設計文件

## 概述

本文件描述 Line 文案分析工具的 API 設計規格，實現文案評分分析功能。

## API Endpoints

### 1. 文案分析 API

#### POST /api/v1/analyze

透過 AI 分析 Line 文案內容，提供評分與改善建議。

**Request Schema:**

```json
{
  "content": "string",           // 必填，Line文案內容，1-2000字
  "target_audience": "enum",    // 必填，目標受眾：B2B, B2C, 電商
  "send_scenario": "enum"       // 必填，發送場景：official_account_push, group_message, one_on_one_service
}
```

**輸入驗證規則:**
- `content`: 字串長度必須在 1-2000 字之間，不可包含惡意腳本
- `target_audience`: 必須是 ["B2B", "B2C", "電商"] 其中之一
- `send_scenario`: 必須是 ["official_account_push", "group_message", "one_on_one_service"] 其中之一

**Response Schema:**

```json
{
  "analysis_id": "string",      // UUID，分析記錄ID
  "status": "string",           // 分析狀態：completed
  "created_at": "datetime",     // 分析時間 (ISO 8601)
  "results": {
    "attractiveness": "number", // 吸引力評分 (1.0-10.0)
    "readability": "number",    // 可讀性評分 (1.0-10.0)
    "line_compatibility": "number", // Line平台相容性評分 (1.0-10.0)
    "overall_score": "number",  // 整體評分 (1.0-10.0)
    "sentiment": "string",      // 情感傾向分析
    "suggestions": ["string"]   // 具體改善建議列表，每項建議為獨立字串
  }
}
```

**HTTP Status Codes:**

- `200 OK`: 分析成功
- `400 Bad Request`: 請求參數錯誤
- `422 Unprocessable Entity`: 輸入驗證失敗
- `500 Internal Server Error`: 內部伺服器錯誤

**錯誤回應格式:**

```json
{
  "error": {
    "code": "string",           // 錯誤代碼
    "message": "string",        // 錯誤訊息
    "details": "object"         // 詳細錯誤資訊 (可選)
  }
}
```

**錯誤代碼說明:**
- `INVALID_CONTENT_LENGTH`: 文案內容長度超出限制 (1-2000字)
- `INVALID_TARGET_AUDIENCE`: 無效的目標受眾選項
- `INVALID_SEND_SCENARIO`: 無效的發送場景選項
- `AI_SERVICE_ERROR`: AI 分析服務錯誤
- `INTERNAL_ERROR`: 系統內部錯誤

### 2. 分析結果查詢 API

#### GET /api/v1/analyze/{analysis_id}

查詢指定分析記錄的結果。

**Path Parameters:**
- `analysis_id`: UUID 格式的分析記錄識別碼

**Response:** 同 POST /analyze 的成功回應格式

**HTTP Status Codes:**

- `200 OK`: 查詢成功
- `404 Not Found`: 分析記錄不存在
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

## 3. 多管道發送 API

### POST /api/v1/send-message

透過多種管道（Line Bot、SMS、Email）發送訊息，支援單發和批次發送。

**Request Schema:**

```json
{
  "content": "string",              // 必填，發送內容
  "channel": "string",              // 必填，發送管道：line, sms, email
  "recipients": [                   // 必填，收件人列表
    {
      "type": "string",             // 收件人類型：line, sms, email
      "id": "string"                // 收件人ID（Line用戶ID、手機號碼、Email地址）
    }
  ],
  "batch_name": "string",           // 可選，批次名稱
  "send_delay": "number"            // 可選，發送延遲秒數，預設0
}
```

**輸入驗證規則:**
- `content`: 字串長度必須在 1-2000 字之間
- `channel`: 必須是 ["line", "sms", "email"] 其中之一
- `recipients`: 陣列長度必須在 1-1000 之間
- `recipients[].type`: 必須是 ["line", "sms", "email"] 其中之一
- `recipients[].id`: 根據類型驗證格式
- `send_delay`: 數字必須 >= 0

**Response Schema:**

```json
{
  "batch_id": "string",             // UUID，批次ID
  "status": "string",               // 批次狀態：pending, processing, completed, failed
  "total_count": "number",          // 發送總數
  "message": "string",              // 回應訊息
  "created_at": "datetime"          // 建立時間 (ISO 8601)
}
```

**HTTP Status Codes:**

- `200 OK`: 發送請求已接受
- `400 Bad Request`: 請求參數錯誤
- `422 Unprocessable Entity`: 輸入驗證失敗
- `500 Internal Server Error`: 內部伺服器錯誤

**錯誤代碼說明:**
- `INVALID_CONTENT_LENGTH`: 發送內容長度超出限制
- `INVALID_CHANNEL`: 無效的發送管道
- `INVALID_RECIPIENTS`: 收件人格式錯誤
- `RECIPIENTS_LIMIT_EXCEEDED`: 收件人數量超出限制
- `CHANNEL_SERVICE_ERROR`: 發送管道服務錯誤


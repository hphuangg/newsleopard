# 資料庫設計文件

## 資料表設計

### analysis_records (分析記錄表)

儲存每次文案分析的完整記錄。

#### 表格結構

| 欄位名稱 | 資料類型 | 限制 | 說明 |
|---------|---------|------|------|
| id | BIGSERIAL | PRIMARY KEY | 內部連續ID |
| analysis_id | UUID | UNIQUE NOT NULL | 對外分析記錄識別碼 |
| content | TEXT | NOT NULL | Line文案內容 |
| target_audience | VARCHAR(50) | NOT NULL | 目標受眾 |
| send_scenario | VARCHAR(50) | NOT NULL | 發送場景 |
| attractiveness | DECIMAL(3,1) | NULL | 吸引力評分 (1.0-10.0) |
| readability | DECIMAL(3,1) | NULL | 可讀性評分 (1.0-10.0) |
| line_compatibility | DECIMAL(3,1) | NULL | Line平台相容性評分 (1.0-10.0) |
| overall_score | DECIMAL(3,1) | NULL | 整體評分 (1.0-10.0) |
| sentiment | VARCHAR(100) | NULL | 情感傾向分析 |
| suggestions | JSONB | NULL | 改善建議列表，格式：["建議1", "建議2", ...] |
| ai_model_used | VARCHAR(100) | NULL | 使用的AI模型名稱 |
| processing_time | DECIMAL(6,3) | NULL | 處理時間(秒) |
| status | VARCHAR(20) | NOT NULL DEFAULT 'pending' | 處理狀態 |
| error_message | TEXT | NULL | 錯誤訊息 |
| created_at | TIMESTAMP | NOT NULL DEFAULT NOW() | 建立時間 |
| updated_at | TIMESTAMP | NOT NULL DEFAULT NOW() | 更新時間 |

#### 建表 SQL

```sql
CREATE TABLE analysis_records (
    id BIGSERIAL PRIMARY KEY,
    analysis_id UUID UNIQUE NOT NULL DEFAULT gen_random_uuid(),
    content TEXT NOT NULL,
    target_audience VARCHAR(50) NOT NULL,
    send_scenario VARCHAR(50) NOT NULL,
    
    -- 分析結果
    attractiveness DECIMAL(3,1) CHECK (attractiveness >= 1.0 AND attractiveness <= 10.0),
    readability DECIMAL(3,1) CHECK (readability >= 1.0 AND readability <= 10.0),
    line_compatibility DECIMAL(3,1) CHECK (line_compatibility >= 1.0 AND line_compatibility <= 10.0),
    overall_score DECIMAL(3,1) CHECK (overall_score >= 1.0 AND overall_score <= 10.0),
    sentiment VARCHAR(100),
    suggestions JSONB,
    
    -- AI 處理資訊
    ai_model_used VARCHAR(100),
    processing_time DECIMAL(6,3) CHECK (processing_time >= 0),
    
    -- 狀態管理
    status VARCHAR(20) NOT NULL DEFAULT 'pending' 
        CHECK (status IN ('pending', 'processing', 'completed', 'failed')),
    error_message TEXT,
    
    -- 時間戳記
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);
```

#### 索引設計

```sql
-- 基礎查詢索引
CREATE INDEX idx_analysis_records_analysis_id ON analysis_records(analysis_id);
CREATE INDEX idx_analysis_records_status ON analysis_records(status);
CREATE INDEX idx_analysis_records_created_at ON analysis_records(created_at);
CREATE INDEX idx_analysis_records_status_created_at ON analysis_records(status, created_at DESC);
```

## 查詢設計

### 內部系統使用連續ID
```sql
-- 內部查詢使用連續ID (效能佳)
SELECT * FROM analysis_records WHERE id = 12345;

-- 批量查詢
SELECT * FROM analysis_records WHERE id BETWEEN 1000 AND 2000;
```

### 對外API使用UUID
```sql
-- API查詢使用UUID (安全性佳)
SELECT * FROM analysis_records WHERE analysis_id = '550e8400-e29b-41d4-a716-446655440000';
```
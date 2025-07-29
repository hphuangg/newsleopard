# 資料庫設計文件

## 資料表設計

## 1. 文案分析相關資料表

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

## 2. 多管道發送相關資料表

### 資料表關聯圖

```
batch_send_records (批次記錄表)
    ↑ (1:N)
    └── message_send_records (發送記錄表)
```

### batch_send_records (批次記錄表)

儲存每次批次發送的統計資訊和狀態。

#### 表格結構

| 欄位名稱 | 資料類型 | 限制 | 說明 |
|---------|---------|------|------|
| id | BIGSERIAL | PRIMARY KEY | 內部連續ID |
| batch_id | UUID | UNIQUE NOT NULL | 對外批次識別碼 |
| batch_name | VARCHAR(255) | NULL | 批次名稱 |
| total_count | INTEGER | NOT NULL | 發送總數 |
| success_count | INTEGER | NOT NULL DEFAULT 0 | 成功數量 |
| failed_count | INTEGER | NOT NULL DEFAULT 0 | 失敗數量 |
| pending_count | INTEGER | NOT NULL DEFAULT 0 | 待處理數量 |
| status | VARCHAR(20) | NOT NULL DEFAULT 'pending' | 批次狀態 |
| version | INTEGER | NOT NULL DEFAULT 0 | 樂觀鎖版本號 |
| created_at | TIMESTAMP | NOT NULL DEFAULT NOW() | 建立時間 |
| updated_at | TIMESTAMP | NOT NULL DEFAULT NOW() | 更新時間 |

#### 建表 SQL

```sql
CREATE TABLE batch_send_records (
    id BIGSERIAL PRIMARY KEY,
    batch_id UUID UNIQUE NOT NULL DEFAULT gen_random_uuid(),
    batch_name VARCHAR(255),
    total_count INTEGER NOT NULL CHECK (total_count > 0),
    success_count INTEGER NOT NULL DEFAULT 0 CHECK (success_count >= 0),
    failed_count INTEGER NOT NULL DEFAULT 0 CHECK (failed_count >= 0),
    pending_count INTEGER NOT NULL DEFAULT 0 CHECK (pending_count >= 0),
    status VARCHAR(20) NOT NULL DEFAULT 'pending' 
        CHECK (status IN ('pending', 'processing', 'completed', 'failed')),
    version INTEGER NOT NULL DEFAULT 0 CHECK (version >= 0),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);
```

### message_send_records (發送記錄表)

儲存每筆訊息的發送詳情。

#### 表格結構

| 欄位名稱 | 資料類型 | 限制 | 說明 |
|---------|---------|------|------|
| id | BIGSERIAL | PRIMARY KEY | 內部連續ID |
| batch_id | UUID | NOT NULL | 批次ID（FK 到 batch_send_records） |
| channel | VARCHAR(20) | NOT NULL | 發送管道：line, sms, email |
| content | TEXT | NOT NULL | 發送內容 |
| recipient_id | VARCHAR(255) | NOT NULL | 收件人ID |
| recipient_type | VARCHAR(50) | NOT NULL | 收件人類型 |
| status | VARCHAR(20) | NOT NULL DEFAULT 'pending' | 發送狀態 |
| error_message | TEXT | NULL | 錯誤訊息 |
| sent_at | TIMESTAMP | NULL | 實際發送時間 |
| created_at | TIMESTAMP | NOT NULL DEFAULT NOW() | 建立時間 |
| updated_at | TIMESTAMP | NOT NULL DEFAULT NOW() | 更新時間 |

#### 建表 SQL

```sql
CREATE TABLE message_send_records (
    id BIGSERIAL PRIMARY KEY,
    batch_id UUID NOT NULL,
    channel VARCHAR(20) NOT NULL 
        CHECK (channel IN ('line', 'sms', 'email')),
    content TEXT NOT NULL,
    recipient_id VARCHAR(255) NOT NULL,
    recipient_type VARCHAR(50) NOT NULL 
        CHECK (recipient_type IN ('line', 'sms', 'email')),
    status VARCHAR(20) NOT NULL DEFAULT 'pending' 
        CHECK (status IN ('pending', 'sending', 'success', 'failed')),
    error_message TEXT,
    sent_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    
    -- 外鍵約束
    FOREIGN KEY (batch_id) REFERENCES batch_send_records(batch_id)
);
```

### 索引設計

```sql
-- 批次記錄表索引
CREATE INDEX idx_batch_send_records_batch_id ON batch_send_records(batch_id);
CREATE INDEX idx_batch_send_records_status ON batch_send_records(status);
CREATE INDEX idx_batch_send_records_created_at ON batch_send_records(created_at);

-- 發送記錄表索引
CREATE INDEX idx_message_send_records_batch_id ON message_send_records(batch_id);
CREATE INDEX idx_message_send_records_status ON message_send_records(status);
CREATE INDEX idx_message_send_records_channel ON message_send_records(channel);
CREATE INDEX idx_message_send_records_created_at ON message_send_records(created_at);

-- 複合索引（用於統計查詢）
CREATE INDEX idx_message_batch_status ON message_send_records(batch_id, status);
CREATE INDEX idx_message_channel_status ON message_send_records(channel, status);
CREATE INDEX idx_message_channel_created_at ON message_send_records(channel, created_at DESC);
```

### 外鍵約束

```sql
-- 發送記錄表的外鍵約束
ALTER TABLE message_send_records 
ADD CONSTRAINT fk_message_batch 
FOREIGN KEY (batch_id) REFERENCES batch_send_records(batch_id)
ON DELETE CASCADE;
```

## 3. 統計更新機制

### 樂觀鎖版本控制

`batch_send_records` 表中的 `version` 欄位用於樂觀鎖控制：

```sql
-- 樂觀鎖更新範例
UPDATE batch_send_records 
SET 
    success_count = success_count + 1,
    version = version + 1,
    updated_at = NOW()
WHERE batch_id = $1 AND version = $2;
```

### Trigger 備用機制

建立 Trigger 函數和觸發器作為統計更新的備用機制：

```sql
-- 建立 Trigger 函數
CREATE OR REPLACE FUNCTION update_batch_stats_backup()
RETURNS TRIGGER AS $$
BEGIN
    -- 只在狀態變更時觸發
    IF NEW.status != OLD.status THEN
        UPDATE batch_send_records 
        SET 
            success_count = (
                SELECT COUNT(*) 
                FROM message_send_records 
                WHERE batch_id = NEW.batch_id AND status = 'success'
            ),
            failed_count = (
                SELECT COUNT(*) 
                FROM message_send_records 
                WHERE batch_id = NEW.batch_id AND status = 'failed'
            ),
            pending_count = (
                SELECT COUNT(*) 
                FROM message_send_records 
                WHERE batch_id = NEW.batch_id AND status = 'pending'
            ),
            version = version + 1,
            updated_at = NOW()
        WHERE batch_id = NEW.batch_id;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 建立 Trigger（預設停用）
CREATE TRIGGER trigger_update_batch_stats_backup
    AFTER UPDATE ON message_send_records
    FOR EACH ROW
    EXECUTE FUNCTION update_batch_stats_backup();

-- 預設停用 Trigger
ALTER TABLE message_send_records 
DISABLE TRIGGER trigger_update_batch_stats_backup;
```

### 統計一致性檢查

```sql
-- 檢查統計一致性的查詢
SELECT 
    b.batch_id,
    b.success_count as stored_success,
    b.failed_count as stored_failed,
    b.pending_count as stored_pending,
    COUNT(*) FILTER (WHERE m.status = 'success') as actual_success,
    COUNT(*) FILTER (WHERE m.status = 'failed') as actual_failed,
    COUNT(*) FILTER (WHERE m.status = 'pending') as actual_pending,
    b.success_count = COUNT(*) FILTER (WHERE m.status = 'success') as success_match,
    b.failed_count = COUNT(*) FILTER (WHERE m.status = 'failed') as failed_match,
    b.pending_count = COUNT(*) FILTER (WHERE m.status = 'pending') as pending_match
FROM batch_send_records b
LEFT JOIN message_send_records m ON b.batch_id = m.batch_id
GROUP BY b.batch_id, b.success_count, b.failed_count, b.pending_count;
```

## 效能優化策略

### 1. 分割資料表（建議）

對於高頻發送場景，建議依時間分割 `message_send_records` 表：

```sql
-- 按月分割範例
CREATE TABLE message_send_records_202401 
PARTITION OF message_send_records 
FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');
```

### 2. 歸檔策略

```sql
-- 歸檔舊記錄（保留3個月）
DELETE FROM message_send_records 
WHERE created_at < NOW() - INTERVAL '3 months';

DELETE FROM batch_send_records 
WHERE created_at < NOW() - INTERVAL '3 months'
AND NOT EXISTS (
    SELECT 1 FROM message_send_records 
    WHERE batch_id = batch_send_records.batch_id
);
```
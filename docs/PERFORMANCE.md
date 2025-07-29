# 效能與統計更新架構設計文件

## 概述

本文件描述多管道發送系統的統計更新架構設計，採用混合方案確保效能和資料一致性。

## 混合統計更新架構

### 設計理念

1. **效能優先**：樂觀鎖作為主要更新機制，提供最佳效能
2. **可靠性保證**：PostgreSQL Trigger 作為備用機制，確保資料一致性
3. **完整監控**：記錄所有關鍵指標，便於效能調優和故障排除

### 架構圖

```
發送狀態更新
    ↓
1. 更新 message_send_records
    ↓
2. 嘗試樂觀鎖更新 batch_send_records
    ↓
成功？ → YES → 完成
    ↓ NO
3. 觸發 Trigger 重新計算
    ↓
完成
```

## 1. 樂觀鎖主要更新機制

### 版本控制設計

樂觀鎖透過版本號控制並發更新，避免資料競爭：

```sql
-- batch_send_records 表已包含版本號欄位
-- version INTEGER DEFAULT 0  -- 樂觀鎖版本號
```

### 樂觀鎖更新邏輯

```python
class BatchStatsService:
    """批次統計服務 - 樂觀鎖實作"""
    
    async def update_batch_stats_optimistic(
        self, 
        batch_id: str, 
        old_status: str, 
        new_status: str
    ) -> bool:
        """使用樂觀鎖更新批次統計"""
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                # 讀取當前批次資料（包含版本號）
                batch = await self.get_batch_by_id(batch_id)
                if not batch:
                    return False
                
                # 計算新的統計數字
                new_stats = self._calculate_new_stats(batch, old_status, new_status)
                
                # 嘗試更新（使用版本號檢查）
                query = """
                    UPDATE batch_send_records 
                    SET 
                        success_count = $1,
                        failed_count = $2,
                        pending_count = $3,
                        version = version + 1,
                        updated_at = NOW()
                    WHERE batch_id = $4 AND version = $5
                """
                
                result = await self.db.execute(
                    query,
                    new_stats['success_count'],
                    new_stats['failed_count'], 
                    new_stats['pending_count'],
                    batch_id,
                    batch.version
                )
                
                if result.rowcount > 0:
                    # 更新成功
                    await self.metrics.record_optimistic_success(batch_id, time.time() - start_time)
                    return True
                else:
                    # 版本衝突，重試
                    await asyncio.sleep(0.01 * (2 ** attempt))  # 指數退避
                    
            except Exception as e:
                logger.warning(f"Optimistic lock attempt {attempt + 1} failed: {e}")
                await self.metrics.record_optimistic_retry(batch_id, attempt + 1)
                
        # 所有重試都失敗
        await self.metrics.record_optimistic_failure(batch_id, max_retries)
        return False
    
    def _calculate_new_stats(self, batch, old_status: str, new_status: str) -> dict:
        """計算新的統計數字"""
        stats = {
            'success_count': batch.success_count,
            'failed_count': batch.failed_count,
            'pending_count': batch.pending_count
        }
        
        # 減少舊狀態計數
        if old_status in stats:
            old_key = f"{old_status}_count"
            if old_key in stats:
                stats[old_key] = max(0, stats[old_key] - 1)
        
        # 增加新狀態計數  
        if new_status in stats:
            new_key = f"{new_status}_count"
            if new_key in stats:
                stats[new_key] += 1
                
        return stats
```

### 重試策略

- **最大重試次數**: 3 次
- **退避策略**: 指數退避（0.01s, 0.02s, 0.04s）
- **失敗處理**: 記錄失敗指標，觸發備用機制

## 2. Trigger 備用機制

### PostgreSQL Trigger 設計

當樂觀鎖更新失敗時，使用 Trigger 重新計算統計：

```sql
-- 建立 Trigger 函數
CREATE OR REPLACE FUNCTION update_batch_stats_backup()
RETURNS TRIGGER AS $$
BEGIN
    -- 只在狀態變更時觸發，避免不必要的計算
    IF NEW.status != OLD.status THEN
        
        -- 重新計算所有統計數字
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
            version = version + 1,  -- 更新版本號
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

-- 預設停用 Trigger，只在需要時啟用
ALTER TABLE message_send_records DISABLE TRIGGER trigger_update_batch_stats_backup;
```

### 動態觸發機制

```python
class HybridStatsUpdater:
    """混合統計更新器"""
    
    async def update_send_status(self, record_id: int, new_status: str):
        """混合統計更新策略"""
        
        # 1. 獲取舊狀態和批次ID
        record = await self.get_send_record(record_id)
        old_status = record.status
        batch_id = record.batch_id
        
        # 2. 更新發送記錄
        await self.update_record_status(record_id, new_status)
        
        # 3. 嘗試樂觀鎖更新
        success = await self.batch_stats_service.update_batch_stats_optimistic(
            batch_id, old_status, new_status
        )
        
        if not success:
            # 4. 樂觀鎖失敗，使用 Trigger 重新計算
            logger.warning(f"Optimistic lock failed for batch {batch_id}, triggering recalculation")
            await self.trigger_stats_recalculation(batch_id)
    
    async def trigger_stats_recalculation(self, batch_id: str):
        """觸發統計重新計算"""
        try:
            # 臨時啟用 Trigger
            await self.db.execute("ALTER TABLE message_send_records ENABLE TRIGGER trigger_update_batch_stats_backup")
            
            # 觸發一次更新，讓 Trigger 重新計算
            await self.db.execute("""
                UPDATE message_send_records 
                SET updated_at = NOW() 
                WHERE batch_id = $1 
                LIMIT 1
            """, batch_id)
            
            # 記錄觸發重新計算的指標
            await self.metrics.record_trigger_recalculation(batch_id)
            
        finally:
            # 重新停用 Trigger
            await self.db.execute("ALTER TABLE message_send_records DISABLE TRIGGER trigger_update_batch_stats_backup")
```

## 3. 效能監控機制

### 監控指標設計

```python
class StatsUpdateMetrics:
    """統計更新效能監控"""
    
    def __init__(self, metrics_client):
        self.metrics_client = metrics_client
    
    async def record_optimistic_success(self, batch_id: str, duration: float):
        """記錄樂觀鎖成功"""
        await self.metrics_client.increment("stats_update.optimistic.success")
        await self.metrics_client.timing("stats_update.optimistic.duration", duration)
        await self.metrics_client.histogram("stats_update.optimistic.duration_hist", duration)
    
    async def record_optimistic_failure(self, batch_id: str, retry_count: int):
        """記錄樂觀鎖失敗"""
        await self.metrics_client.increment("stats_update.optimistic.failure")
        await self.metrics_client.increment("stats_update.optimistic.total_retries", retry_count)
    
    async def record_optimistic_retry(self, batch_id: str, attempt: int):
        """記錄樂觀鎖重試"""
        await self.metrics_client.increment(f"stats_update.optimistic.retry.attempt_{attempt}")
    
    async def record_trigger_recalculation(self, batch_id: str):
        """記錄觸發重新計算"""
        await self.metrics_client.increment("stats_update.trigger.recalculation")
        
    async def record_version_conflict(self, batch_id: str):
        """記錄版本衝突"""
        await self.metrics_client.increment("stats_update.version.conflict")
        
    async def get_stats_update_metrics(self) -> dict:
        """獲取統計更新指標摘要"""
        return {
            "optimistic_success_rate": await self._calculate_success_rate(),
            "average_retry_count": await self._calculate_average_retries(),
            "trigger_usage_rate": await self._calculate_trigger_usage(),
            "version_conflict_rate": await self._calculate_conflict_rate()
        }
```

### 告警機制

```python
class StatsUpdateAlerting:
    """統計更新告警"""
    
    async def check_optimistic_lock_health(self):
        """檢查樂觀鎖健康狀態"""
        
        # 檢查成功率
        success_rate = await self.metrics.get_optimistic_success_rate(last_minutes=5)
        if success_rate < 0.8:  # 成功率低於80%
            await self.send_alert(
                "Optimistic lock success rate too low", 
                f"Success rate: {success_rate:.2%}"
            )
        
        # 檢查平均重試次數
        avg_retries = await self.metrics.get_average_retry_count(last_minutes=5)
        if avg_retries > 2:  # 平均重試超過2次
            await self.send_alert(
                "High retry count detected", 
                f"Average retries: {avg_retries:.1f}"
            )
        
        # 檢查 Trigger 使用率
        trigger_rate = await self.metrics.get_trigger_usage_rate(last_minutes=5)
        if trigger_rate > 0.1:  # Trigger使用率超過10%
            await self.send_alert(
                "High trigger usage detected", 
                f"Trigger usage rate: {trigger_rate:.2%}"
            )
```

## 4. 效能比較分析

### 更新機制效能對比

| 機制 | 平均延遲 | 吞吐量 | 資源消耗 | 資料一致性 |
|------|----------|--------|----------|------------|
| 樂觀鎖 | ~1ms | 高 | 低 | 最終一致 |
| Trigger | ~5ms | 中 | 高 | 強一致 |
| 混合方案 | ~1.2ms | 高 | 低-中 | 強一致 |

### 並發場景分析

```python
# 高並發測試場景
async def benchmark_stats_update():
    """統計更新效能基準測試"""
    
    batch_id = "test-batch-001"
    concurrent_updates = 100
    
    # 測試樂觀鎖效能
    start_time = time.time()
    tasks = [
        update_send_status(f"record_{i}", "success") 
        for i in range(concurrent_updates)
    ]
    await asyncio.gather(*tasks)
    optimistic_duration = time.time() - start_time
    
    logger.info(f"Optimistic lock: {concurrent_updates} updates in {optimistic_duration:.2f}s")
    logger.info(f"Average: {(optimistic_duration / concurrent_updates) * 1000:.2f}ms per update")
```

## 5. 實作指南

### 部署步驟

1. **建立 Trigger 函數**
```sql
-- 執行 Trigger 建立腳本
\i create_trigger_functions.sql
```

2. **配置監控**
```python
# 初始化監控
metrics = StatsUpdateMetrics(prometheus_client)
alerting = StatsUpdateAlerting(alert_manager)

# 啟動健康檢查
asyncio.create_task(alerting.health_check_loop())
```

3. **調優參數**
```python
# 設定樂觀鎖參數
OPTIMISTIC_LOCK_MAX_RETRIES = 3
OPTIMISTIC_LOCK_BACKOFF_BASE = 0.01  # 10ms

# 設定告警閾值
OPTIMISTIC_SUCCESS_RATE_THRESHOLD = 0.8
TRIGGER_USAGE_RATE_THRESHOLD = 0.1
```

### 故障排除指南

#### 常見問題

1. **樂觀鎖成功率低**
   - 檢查並發負載是否過高
   - 調整重試參數和退避策略
   - 考慮批次大小優化

2. **Trigger 使用率高**
   - 檢查資料庫連接池設定
   - 分析並發模式
   - 考慮分散負載

3. **統計不準確**
   - 檢查 Trigger 函數邏輯
   - 驗證樂觀鎖計算邏輯
   - 執行資料一致性檢查

#### 除錯工具

```python
async def validate_batch_stats(batch_id: str):
    """驗證批次統計準確性"""
    
    # 從批次表讀取統計
    batch_stats = await get_batch_stats(batch_id)
    
    # 從發送記錄重新計算
    actual_stats = await calculate_actual_stats(batch_id)
    
    # 比較結果
    discrepancies = []
    for key in ['success_count', 'failed_count', 'pending_count']:
        if batch_stats[key] != actual_stats[key]:
            discrepancies.append({
                'field': key,
                'stored': batch_stats[key],
                'actual': actual_stats[key]
            })
    
    if discrepancies:
        logger.error(f"Stats discrepancies found for batch {batch_id}: {discrepancies}")
        # 自動修復
        await fix_batch_stats(batch_id, actual_stats)
    
    return len(discrepancies) == 0
```

## 總結

混合統計更新架構結合了樂觀鎖的高效能和 Trigger 的可靠性，為多管道發送系統提供了最佳的統計更新解決方案。透過完整的監控和告警機制，確保系統在各種負載條件下都能穩定運行。
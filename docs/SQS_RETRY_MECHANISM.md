# SQS 重試機制與失敗處理

## 問題描述

原本的 SQS 佇列沒有配置 Dead Letter Queue (DLQ)，導致發送失敗的訊息會無限重試，造成系統資源浪費。

## 解決方案

### 1. DLQ 配置

現在所有 SQS 佇列都配置了 DLQ 重定向策略：

- **maxReceiveCount: 3** - 訊息失敗 3 次後會被移到 DLQ
- **send-queue** → **send-dlq** (單一訊息失敗佇列)  
- **batch-queue** → **batch-dlq** (批次訊息失敗佇列)

### 2. 重試流程

```
訊息發送失敗
↓
重試 #1 (失敗)
↓
重試 #2 (失敗)
↓
重試 #3 (失敗)
↓
移動到 DLQ ✅
```

### 3. 初始化腳本

**`scripts/init-sqs.sh`**
- 自動建立所有必要的 SQS 佇列
- 配置正確的 DLQ 重定向策略
- 驗證配置是否正確

使用方法：
```bash
./scripts/init-sqs.sh
```

### 4. 監控腳本

**`scripts/check-dlq.sh`**
- 檢查 DLQ 中失敗訊息的數量
- 顯示失敗訊息的範例內容
- 提供清理 DLQ 的指令

使用方法：
```bash
./scripts/check-dlq.sh
```

## 失敗原因分析

常見的訊息發送失敗原因：

1. **Line Bot Token 無效或過期**
2. **收件人 ID 格式錯誤或無效** 
3. **Line Bot API 連接超時**
4. **頻率限制達到上限**
5. **網路連接問題**

## 故障排除

### 檢查失敗訊息

```bash
# 查看 DLQ 狀態
./scripts/check-dlq.sh

# 手動查看失敗訊息
aws --endpoint-url=http://localhost:4566 sqs receive-message \
  --queue-url http://sqs.us-east-1.localhost.localstack.cloud:4566/000000000000/send-dlq
```

### 重新處理失敗訊息

如果修復了問題（例如更新了 Line Bot Token），可以將 DLQ 中的訊息重新送回主佇列：

```bash
# 從 DLQ 接收訊息
MESSAGE=$(aws --endpoint-url=http://localhost:4566 sqs receive-message \
  --queue-url http://sqs.us-east-1.localhost.localstack.cloud:4566/000000000000/send-dlq \
  --query 'Messages[0].Body' --output text)

# 重新發送到主佇列
aws --endpoint-url=http://localhost:4566 sqs send-message \
  --queue-url http://sqs.us-east-1.localhost.localstack.cloud:4566/000000000000/send-queue \
  --message-body "$MESSAGE"
```

### 清理 DLQ

修復問題後，清理 DLQ 中的失敗訊息：

```bash
# 清空 send-dlq
aws --endpoint-url=http://localhost:4566 sqs purge-queue \
  --queue-url http://sqs.us-east-1.localhost.localstack.cloud:4566/000000000000/send-dlq

# 清空 batch-dlq  
aws --endpoint-url=http://localhost:4566 sqs purge-queue \
  --queue-url http://sqs.us-east-1.localhost.localstack.cloud:4566/000000000000/batch-dlq
```

## 監控指標

建議監控以下指標：

1. **DLQ 訊息數量** - 應該保持在低水平
2. **重試次數** - 高重試率可能表示系統問題
3. **發送成功率** - 應該維持在高水平（>95%）

## 生產環境注意事項

1. **設定適當的 maxReceiveCount** - 根據業務需求調整（建議 3-5 次）
2. **監控 DLQ** - 設定告警機制監控 DLQ 訊息數量
3. **定期檢視失敗原因** - 分析 DLQ 中的訊息找出根本原因
4. **自動重試機制** - 考慮實作自動重試已修復問題的失敗訊息

## 相關檔案

- `scripts/init-sqs.sh` - SQS 初始化腳本
- `scripts/check-dlq.sh` - DLQ 監控腳本  
- `shared/utils/sqs_client.py` - SQS 客戶端實作
- `worker/app/worker.py` - Worker 主程式
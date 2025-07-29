# 🚀 AWS SQS 佇列系統設置指南

## 📋 概述

本專案使用 AWS SQS 作為訊息佇列系統，支援本地開發 (LocalStack) 和生產環境 (AWS SQS)。

## 🏗️ 架構設計

### 佇列設計
- **send-queue**: 單一訊息發送 (≤5 個收件人)
- **batch-queue**: 批次訊息發送 (>5 個收件人)
- **send-dlq**: 單一訊息失敗佇列 (DLQ)
- **batch-dlq**: 批次訊息失敗佇列 (DLQ)

### 核心組件
- **SQSConfig**: AWS SQS 客戶端配置
- **SQSQueueManager**: 佇列操作管理
- **SQSWorker**: 訊息處理 Worker
- **SendService**: 發送服務 (整合 SQS)

## 🔧 本地開發設置

### 1. 使用 LocalStack

```bash
# 啟動 LocalStack 和 SQS 初始化
docker-compose -f docker-compose.localstack.yml up -d

# 檢查佇列是否建立成功
docker logs sqs-init
```

### 2. 環境變數配置

建立 `.env` 檔案 (基於 `.env.example`):

```bash
# 複製範例配置
cp .env.example .env

# LocalStack 設定
AWS_ACCESS_KEY_ID=test
AWS_SECRET_ACCESS_KEY=test
AWS_REGION=ap-northeast-1
AWS_SQS_ENDPOINT_URL=http://localhost:4566

# LocalStack SQS URLs
SQS_SEND_QUEUE_URL=http://localhost:4566/000000000000/send-queue
SQS_BATCH_QUEUE_URL=http://localhost:4566/000000000000/batch-queue
SQS_SEND_DLQ_URL=http://localhost:4566/000000000000/send-dlq
SQS_BATCH_DLQ_URL=http://localhost:4566/000000000000/batch-dlq
```

### 3. 安裝依賴

```bash
pip install boto3==1.34.162 botocore==1.34.162 localstack-client==2.5
```

## 🚀 生產環境設置

### 1. AWS SQS 佇列建立

```bash
# 建立 DLQ
aws sqs create-queue --queue-name send-dlq --region ap-northeast-1
aws sqs create-queue --queue-name batch-dlq --region ap-northeast-1

# 取得 DLQ ARNs
SEND_DLQ_ARN=$(aws sqs get-queue-attributes \\
  --queue-url https://sqs.ap-northeast-1.amazonaws.com/YOUR-ACCOUNT/send-dlq \\
  --attribute-names QueueArn --query 'Attributes.QueueArn' --output text)

BATCH_DLQ_ARN=$(aws sqs get-queue-attributes \\
  --queue-url https://sqs.ap-northeast-1.amazonaws.com/YOUR-ACCOUNT/batch-dlq \\
  --attribute-names QueueArn --query 'Attributes.QueueArn' --output text)

# 建立主要佇列 (包含 DLQ 設定)
aws sqs create-queue --queue-name send-queue \\
  --attributes "{\\"RedrivePolicy\\": \\"{\\\\\\"deadLetterTargetArn\\\\\\":\\\\\\"$SEND_DLQ_ARN\\\\\\",\\\\\\"maxReceiveCount\\\\\\":3}\\"}"

aws sqs create-queue --queue-name batch-queue \\
  --attributes "{\\"RedrivePolicy\\": \\"{\\\\\\"deadLetterTargetArn\\\\\\":\\\\\\"$BATCH_DLQ_ARN\\\\\\",\\\\\\"maxReceiveCount\\\\\\":3}\\"}"
```

### 2. 生產環境變數

```bash
# AWS 認證
AWS_ACCESS_KEY_ID=your_actual_access_key
AWS_SECRET_ACCESS_KEY=your_actual_secret_key
AWS_REGION=ap-northeast-1

# 生產 SQS URLs
SQS_SEND_QUEUE_URL=https://sqs.ap-northeast-1.amazonaws.com/YOUR-ACCOUNT/send-queue
SQS_BATCH_QUEUE_URL=https://sqs.ap-northeast-1.amazonaws.com/YOUR-ACCOUNT/batch-queue
SQS_SEND_DLQ_URL=https://sqs.ap-northeast-1.amazonaws.com/YOUR-ACCOUNT/send-dlq
SQS_BATCH_DLQ_URL=https://sqs.ap-northeast-1.amazonaws.com/YOUR-ACCOUNT/batch-dlq
```

## 🔄 使用方式

### 1. 啟動 SQS Worker

```bash
# 啟動 Worker (背景執行)
python sqs_worker.py &

# 或使用 systemd/supervisor 管理
```

### 2. 發送訊息

```python
from app.services.send_service import send_service

# 發送訊息
result = await send_service.send_message(
    content="Hello World",
    channel="line",
    recipients=[
        {"id": "user1"},
        {"id": "user2"}
    ]
)

print(f"Batch ID: {result['batch_id']}")
print(f"Status: {result['status']}")
```

### 3. 監控佇列狀態

```python
from app.services.sqs_queue_manager import sqs_queue_manager

# 取得佇列統計
stats = await sqs_queue_manager.get_queue_statistics()
print(stats)
```

## 🧪 測試

```bash
# 執行 SQS 系統測試
pytest tests/test_sqs_system.py -v

# 執行特定測試
pytest tests/test_sqs_system.py::TestSQSQueueManager::test_send_message_success -v
```

## 📊 監控和日誌

### Worker 日誌

```bash
# 查看 Worker 日誌
tail -f sqs_worker.log

# 查看即時處理狀態
grep "Processing message" sqs_worker.log
```

### 佇列監控

```bash
# LocalStack 佇列狀態
aws --endpoint-url=http://localhost:4566 sqs get-queue-attributes \\
  --queue-url http://localhost:4566/000000000000/send-queue \\
  --attribute-names All

# 生產環境佇列狀態
aws sqs get-queue-attributes \\
  --queue-url https://sqs.ap-northeast-1.amazonaws.com/YOUR-ACCOUNT/send-queue \\
  --attribute-names All
```

## 🚨 故障排除

### 常見問題

1. **佇列連接失敗**
   ```bash
   # 檢查網路連接
   curl -I http://localhost:4566/health
   
   # 檢查 AWS credentials
   aws sts get-caller-identity
   ```

2. **Worker 無法處理訊息**
   ```bash
   # 檢查佇列是否有訊息
   aws --endpoint-url=http://localhost:4566 sqs receive-message \\
     --queue-url http://localhost:4566/000000000000/send-queue
   ```

3. **DLQ 訊息累積**
   ```bash
   # 檢查 DLQ 訊息
   aws --endpoint-url=http://localhost:4566 sqs get-queue-attributes \\
     --queue-url http://localhost:4566/000000000000/send-dlq \\
     --attribute-names ApproximateNumberOfMessages
   ```

### 除錯模式

```bash
# 啟用詳細日誌
export DEBUG=1
python sqs_worker.py
```

## 📈 效能調整

### Worker 設定

```python
# app/workers/sqs_worker.py
class SQSWorker:
    def __init__(self):
        self.max_messages_per_poll = 10  # 每次輪詢最大訊息數
        self.poll_interval = 1           # 輪詢間隔 (秒)
        self.queues_to_process = ['send_queue', 'batch_queue']
```

### 佇列設定

- **VisibilityTimeout**: 300秒 (單一訊息), 600秒 (批次訊息)
- **MessageRetentionPeriod**: 14天
- **MaxReceiveCount**: 3次重試後進入 DLQ

## 🔗 相關文件

- [AWS SQS 官方文檔](https://docs.aws.amazon.com/sqs/)
- [LocalStack SQS 文檔](https://docs.localstack.cloud/user-guide/aws/sqs/)
- [boto3 SQS 文檔](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/sqs.html)
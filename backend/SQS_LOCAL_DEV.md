# 🚀 SQS 本地開發環境設置

## 📋 快速開始

### 1. 啟動 LocalStack

```bash
docker-compose -f docker-compose.localstack-simple.yml up -d
```

### 2. 創建 SQS 佇列

```bash
# 設置環境變數
export AWS_ACCESS_KEY_ID=test
export AWS_SECRET_ACCESS_KEY=test
export AWS_DEFAULT_REGION=us-east-1

# 創建佇列
aws --endpoint-url=http://localhost:4566 sqs create-queue --queue-name send-queue
aws --endpoint-url=http://localhost:4566 sqs create-queue --queue-name batch-queue
aws --endpoint-url=http://localhost:4566 sqs create-queue --queue-name send-dlq
aws --endpoint-url=http://localhost:4566 sqs create-queue --queue-name batch-dlq
```

### 3. 配置環境變數

複製 `.env.localstack` 到 `.env`：

```bash
cp .env.localstack .env
```

### 4. 使用方式

```bash
# 查看佇列狀態
python sqs_monitor.py status

# 啟動 Worker 處理訊息
python sqs_worker.py

# 發送測試訊息（透過 API）
curl -X POST http://localhost:8000/api/v1/send/send-message \
  -H "Content-Type: application/json" \
  -d '{"content":"Hello","channel":"line","recipients":[{"id":"user1"}]}'
```

## 🔧 檔案說明

### 核心檔案
- `docker-compose.localstack-simple.yml` - LocalStack 配置
- `.env.localstack` - 本地開發環境變數
- `sqs_monitor.py` - 佇列監控工具
- `sqs_worker.py` - 訊息處理 Worker

### 環境配置
- `.env` - 當前環境配置
- `.env.example` - 環境配置範例
- `.env.localstack` - LocalStack 專用配置

## 🚨 注意事項

1. LocalStack 需要 Docker 運行
2. 每次重啟 LocalStack 都需要重新創建佇列
3. 佇列 URL 格式：`http://sqs.us-east-1.localhost.localstack.cloud:4566/000000000000/[queue-name]`

## 🔍 監控命令

```bash
# 查看佇列狀態
python sqs_monitor.py status

# 處理所有訊息
python sqs_monitor.py consume

# AWS CLI 查看
aws --endpoint-url=http://localhost:4566 sqs list-queues
```
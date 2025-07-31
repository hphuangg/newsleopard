#!/bin/bash

# SQS 佇列初始化腳本
# 確保 LocalStack SQS 佇列有正確的 DLQ 配置

set -e

ENDPOINT_URL=${AWS_SQS_ENDPOINT_URL:-http://localhost:4566}
REGION=${AWS_REGION:-us-east-1}

echo "🚀 Initializing SQS queues with DLQ configuration..."
echo "Endpoint: $ENDPOINT_URL"
echo "Region: $REGION"

# 等待 LocalStack 就緒
echo "⏳ Waiting for LocalStack to be ready..."
until curl -s "$ENDPOINT_URL/health" | grep -q '"sqs": "available"'; do
    echo "Waiting for SQS service..."
    sleep 2
done
echo "✅ LocalStack SQS is ready!"

# 建立 DLQ
echo "📝 Creating Dead Letter Queues..."
aws --endpoint-url=$ENDPOINT_URL sqs create-queue --queue-name send-dlq --region $REGION || echo "send-dlq already exists"
aws --endpoint-url=$ENDPOINT_URL sqs create-queue --queue-name batch-dlq --region $REGION || echo "batch-dlq already exists"

# 建立主要佇列
echo "📝 Creating main queues..."
aws --endpoint-url=$ENDPOINT_URL sqs create-queue --queue-name send-queue --region $REGION || echo "send-queue already exists"
aws --endpoint-url=$ENDPOINT_URL sqs create-queue --queue-name batch-queue --region $REGION || echo "batch-queue already exists"

# 取得 DLQ ARNs
echo "🔍 Getting DLQ ARNs..."
SEND_DLQ_ARN=$(aws --endpoint-url=$ENDPOINT_URL sqs get-queue-attributes \
    --queue-url "http://sqs.$REGION.localhost.localstack.cloud:4566/000000000000/send-dlq" \
    --attribute-names QueueArn --query 'Attributes.QueueArn' --output text)

BATCH_DLQ_ARN=$(aws --endpoint-url=$ENDPOINT_URL sqs get-queue-attributes \
    --queue-url "http://sqs.$REGION.localhost.localstack.cloud:4566/000000000000/batch-dlq" \
    --attribute-names QueueArn --query 'Attributes.QueueArn' --output text)

echo "Send DLQ ARN: $SEND_DLQ_ARN"
echo "Batch DLQ ARN: $BATCH_DLQ_ARN"

# 設定主要佇列的 DLQ 重定向策略
echo "⚙️  Configuring redrive policies..."

# send-queue DLQ 設定 (失敗 3 次後移到 DLQ)
aws --endpoint-url=$ENDPOINT_URL sqs set-queue-attributes \
    --queue-url "http://sqs.$REGION.localhost.localstack.cloud:4566/000000000000/send-queue" \
    --attributes "{\"RedrivePolicy\":\"{\\\"deadLetterTargetArn\\\":\\\"$SEND_DLQ_ARN\\\",\\\"maxReceiveCount\\\":3}\"}"

# batch-queue DLQ 設定 (失敗 3 次後移到 DLQ)
aws --endpoint-url=$ENDPOINT_URL sqs set-queue-attributes \
    --queue-url "http://sqs.$REGION.localhost.localstack.cloud:4566/000000000000/batch-queue" \
    --attributes "{\"RedrivePolicy\":\"{\\\"deadLetterTargetArn\\\":\\\"$BATCH_DLQ_ARN\\\",\\\"maxReceiveCount\\\":3}\"}"

# 驗證配置
echo "🔍 Verifying queue configurations..."
echo "Send Queue DLQ Configuration:"
aws --endpoint-url=$ENDPOINT_URL sqs get-queue-attributes \
    --queue-url "http://sqs.$REGION.localhost.localstack.cloud:4566/000000000000/send-queue" \
    --attribute-names RedrivePolicy --query 'Attributes.RedrivePolicy' --output text

echo "Batch Queue DLQ Configuration:"
aws --endpoint-url=$ENDPOINT_URL sqs get-queue-attributes \
    --queue-url "http://sqs.$REGION.localhost.localstack.cloud:4566/000000000000/batch-queue" \
    --attribute-names RedrivePolicy --query 'Attributes.RedrivePolicy' --output text

echo "✅ SQS queues initialized successfully!"
echo ""
echo "📋 Queue Summary:"
echo "  - send-queue: Single message queue (max 3 retries → send-dlq)"
echo "  - batch-queue: Batch message queue (max 3 retries → batch-dlq)"
echo "  - send-dlq: Dead letter queue for failed single messages"
echo "  - batch-dlq: Dead letter queue for failed batch messages"
echo ""
echo "🎯 Failed messages will be moved to DLQ after 3 failed attempts."
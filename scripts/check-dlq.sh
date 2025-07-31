#!/bin/bash

# DLQ 監控腳本
# 檢查 Dead Letter Queue 中的失敗訊息

set -e

ENDPOINT_URL=${AWS_SQS_ENDPOINT_URL:-http://localhost:4566}
REGION=${AWS_REGION:-us-east-1}

echo "🔍 Checking Dead Letter Queues..."
echo "Endpoint: $ENDPOINT_URL"
echo "=================================="

# 檢查 send-dlq
echo "📨 Send DLQ Status:"
SEND_DLQ_COUNT=$(aws --endpoint-url=$ENDPOINT_URL sqs get-queue-attributes \
    --queue-url "http://sqs.$REGION.localhost.localstack.cloud:4566/000000000000/send-dlq" \
    --attribute-names ApproximateNumberOfMessages \
    --query 'Attributes.ApproximateNumberOfMessages' --output text)

echo "  Failed messages: $SEND_DLQ_COUNT"

if [ "$SEND_DLQ_COUNT" -gt 0 ]; then
    echo "  📋 Sample failed message:"
    aws --endpoint-url=$ENDPOINT_URL sqs receive-message \
        --queue-url "http://sqs.$REGION.localhost.localstack.cloud:4566/000000000000/send-dlq" \
        --max-number-of-messages 1 --query 'Messages[0].Body' --output text | python3 -m json.tool 2>/dev/null || echo "  (Failed to parse JSON)"
fi

echo ""

# 檢查 batch-dlq
echo "📦 Batch DLQ Status:"
BATCH_DLQ_COUNT=$(aws --endpoint-url=$ENDPOINT_URL sqs get-queue-attributes \
    --queue-url "http://sqs.$REGION.localhost.localstack.cloud:4566/000000000000/batch-dlq" \
    --attribute-names ApproximateNumberOfMessages \
    --query 'Attributes.ApproximateNumberOfMessages' --output text)

echo "  Failed messages: $BATCH_DLQ_COUNT"

if [ "$BATCH_DLQ_COUNT" -gt 0 ]; then
    echo "  📋 Sample failed message:"
    aws --endpoint-url=$ENDPOINT_URL sqs receive-message \
        --queue-url "http://sqs.$REGION.localhost.localstack.cloud:4566/000000000000/batch-dlq" \
        --max-number-of-messages 1 --query 'Messages[0].Body' --output text | python3 -m json.tool 2>/dev/null || echo "  (Failed to parse JSON)"
fi

echo ""
echo "📊 Summary:"
echo "  - Send DLQ: $SEND_DLQ_COUNT failed messages"
echo "  - Batch DLQ: $BATCH_DLQ_COUNT failed messages"
echo "  - Total failed: $((SEND_DLQ_COUNT + BATCH_DLQ_COUNT)) messages"

if [ $((SEND_DLQ_COUNT + BATCH_DLQ_COUNT)) -gt 0 ]; then
    echo ""
    echo "⚠️  There are failed messages in DLQ that need attention!"
    echo "   Consider investigating the failure reasons and fixing the issues."
    echo ""
    echo "💡 To clear DLQ messages (after fixing issues):"
    echo "   aws --endpoint-url=$ENDPOINT_URL sqs purge-queue --queue-url http://sqs.$REGION.localhost.localstack.cloud:4566/000000000000/send-dlq"
    echo "   aws --endpoint-url=$ENDPOINT_URL sqs purge-queue --queue-url http://sqs.$REGION.localhost.localstack.cloud:4566/000000000000/batch-dlq"
else
    echo "✅ No failed messages in DLQ - all good!"
fi
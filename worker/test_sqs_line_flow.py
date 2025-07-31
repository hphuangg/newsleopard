#!/usr/bin/env python3
"""
SQS + Line Bot 完整流程測試

這個腳本會：
1. 發送測試訊息到 SQS 佇列
2. 驗證 Worker 是否能正確接收並透過 Line Bot 發送
"""

import asyncio
import json
import logging
import sys
import uuid
from pathlib import Path

# 添加根目錄到路徑
sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.utils.sqs_client import SQSClient
from shared.config.settings import settings


def setup_logging():
    """設定日誌"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)


def create_test_message():
    """建立測試訊息"""
    message_id = str(uuid.uuid4())
    batch_id = str(uuid.uuid4())
    
    # 測試訊息資料
    message_data = {
        "message_id": message_id,
        "batch_id": batch_id,
        "channel": "line",
        "content": f"🧪 測試訊息 from SQS\n\n訊息 ID: {message_id}\n批次 ID: {batch_id}",
        "recipient": {"id": "U1d4ee13114158ba0798e54ff370570b3", "type": "default"},
        "created_at": "2024-01-01T12:00:00Z"
    }
    
    return message_data


async def test_sqs_send():
    """測試發送訊息到 SQS"""
    logger = setup_logging()
    
    logger.info("🚀 Testing SQS + Line Bot integration...")
    
    try:
        # 建立 SQS 客戶端
        logger.info("📡 Initializing SQS client...")
        sqs_client = SQSClient()
        
        # 測試 SQS 連接
        if not sqs_client.test_connection():
            logger.error("❌ SQS connection test failed")
            return False
        
        logger.info("✅ SQS connection established")
        
        # 建立測試訊息
        test_message = create_test_message()
        logger.info(f"📝 Created test message: {test_message['message_id']}")
        
        # 發送到 send_queue
        logger.info("📤 Sending message to send_queue...")
        
        message_id = sqs_client.send_message(
            queue_name='send_queue',
            message_data=test_message
        )
        success = message_id is not None
        
        if success:
            logger.info("✅ Message sent to SQS successfully!")
            logger.info(f"🔍 Message details:")
            logger.info(f"   - Message ID: {test_message['message_id']}")
            logger.info(f"   - Batch ID: {test_message['batch_id']}")
            logger.info(f"   - Channel: {test_message['channel']}")
            logger.info(f"   - Recipient: {test_message['recipient']}")
            logger.info(f"   - Content: {test_message['content']}")
            
            logger.info("🔔 Now start the worker to process this message:")
            logger.info("   cd worker && python -m app.worker")
            
            return True
        else:
            logger.error("❌ Failed to send message to SQS")
            return False
            
    except Exception as e:
        logger.error(f"💥 Test failed with error: {e}")
        return False


async def test_batch_message():
    """測試批次訊息"""
    logger = setup_logging()
    
    logger.info("📦 Testing batch message...")
    
    try:
        sqs_client = SQSClient()
        
        batch_id = str(uuid.uuid4())
        
        # 建立批次訊息
        batch_message = {
            "batch_id": batch_id,
            "channel": "line",
            "content": f"📦 批次測試訊息\n\n批次 ID: {batch_id}",
            "recipients": [
                {
                    "id": "recipient_1",
                    "message_id": str(uuid.uuid4()),
                    "user_id": "U1d4ee13114158ba0798e54ff370570b3"
                },
                {
                    "id": "recipient_2", 
                    "message_id": str(uuid.uuid4()),
                    "user_id": "U1d4ee13114158ba0798e54ff370570b3"  # 同一個用戶測試批次發送
                }
            ],
            "created_at": "2024-01-01T12:00:00Z"
        }
        
        logger.info(f"📤 Sending batch message to batch_queue...")
        
        message_id = sqs_client.send_message(
            queue_name='batch_queue',
            message_data=batch_message
        )
        success = message_id is not None
        
        if success:
            logger.info("✅ Batch message sent successfully!")
            logger.info(f"📊 Batch details:")
            logger.info(f"   - Batch ID: {batch_id}")
            logger.info(f"   - Recipients: {len(batch_message['recipients'])}")
            return True
        else:
            logger.error("❌ Failed to send batch message")
            return False
            
    except Exception as e:
        logger.error(f"💥 Batch test failed: {e}")
        return False


async def main():
    """主測試函數"""
    logger = setup_logging()
    
    logger.info("🎯 SQS + Line Bot Integration Test")
    logger.info("=" * 60)
    
    # 顯示配置資訊
    logger.info("🔧 Configuration:")
    logger.info(f"   - SQS Endpoint: {settings.aws.sqs_endpoint_url}")
    logger.info(f"   - Send Queue: {settings.sqs.send_queue_url}")
    logger.info(f"   - Batch Queue: {settings.sqs.batch_queue_url}")
    logger.info(f"   - Line Token configured: {'Yes' if settings.line_bot.channel_access_token else 'No'}")
    
    logger.info("-" * 60)
    
    # 執行單一訊息測試
    single_success = await test_sqs_send()
    
    logger.info("-" * 60)
    
    # 執行批次訊息測試
    batch_success = await test_batch_message()
    
    logger.info("=" * 60)
    logger.info(f"📊 Test Results:")
    logger.info(f"   - Single message: {'✅ PASS' if single_success else '❌ FAIL'}")
    logger.info(f"   - Batch message: {'✅ PASS' if batch_success else '❌ FAIL'}")
    
    if single_success and batch_success:
        logger.info("🎉 All tests passed!")
        logger.info("📋 Next steps:")
        logger.info("   1. Start the worker: cd worker && python -m app.worker")
        logger.info("   2. Check worker logs for message processing")
        logger.info("   3. Verify Line messages are sent (if valid token configured)")
        return 0
    else:
        logger.error("💥 Some tests failed!")
        return 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n⚠️  Test interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"💥 Test suite failed: {e}")
        sys.exit(1)
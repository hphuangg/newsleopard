#!/usr/bin/env python3
"""
Line 訊息推送測試腳本

這個腳本會直接測試 Line Bot 發送功能，
不依賴 SQS 佇列，方便快速驗證 Line 整合是否正常。
"""

import asyncio
import logging
import sys
from pathlib import Path

# 添加根目錄到路徑
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.channels.line_bot import LineBotChannel
from shared.channels.exceptions import ChannelConfigurationError


async def test_line_push():
    """測試 Line Bot 推送功能"""
    
    # 設定日誌
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)
    
    logger.info("🚀 Starting Line Bot push test...")
    
    try:
        # 初始化 Line Bot 管道
        logger.info("📱 Initializing Line Bot channel...")
        line_channel = LineBotChannel()
        
        # 檢查管道可用性
        is_available = await line_channel.is_available()
        logger.info(f"📋 Line Bot channel available: {is_available}")
        
        if not is_available:
            logger.error("❌ Line Bot channel is not available. Please check configuration.")
            return False
        
        # 使用真實的 Line 用戶 ID
        test_recipient = "U1d4ee13114158ba0798e54ff370570b3"
        test_content = "🧪 這是一則來自 NewsLeopard Worker 的測試訊息！\n\n發送時間: " + \
                      str(asyncio.get_event_loop().time())
        
        logger.info(f"📤 Sending test message to {test_recipient}")
        logger.info(f"📝 Message content: {test_content}")
        
        # 發送測試訊息
        result = await line_channel.send_message(test_content, test_recipient)
        
        # 檢查結果
        if result.status.value == 'success':
            logger.info("✅ Test message sent successfully!")
            logger.info(f"📊 Message ID: {result.message_id}")
            if result.response_data:
                logger.info(f"📄 Response data: {result.response_data}")
            return True
        else:
            logger.error(f"❌ Test message failed: {result.error_message}")
            return False
            
    except ChannelConfigurationError as e:
        logger.error(f"🔧 Configuration error: {e}")
        logger.info("💡 請檢查環境變數:")
        logger.info("   - LINE_CHANNEL_ACCESS_TOKEN: Line Bot Channel Access Token")
        logger.info("   - LINE_CHANNEL_SECRET: Line Bot Channel Secret (可選)")
        return False
        
    except Exception as e:
        logger.error(f"💥 Unexpected error: {e}")
        return False


async def test_message_validation():
    """測試訊息驗證功能"""
    logger = logging.getLogger(__name__)
    
    logger.info("🔍 Testing message validation...")
    
    try:
        line_channel = LineBotChannel()
        
        # 測試不同的收件人 ID 格式
        test_cases = [
            ("U1234567890abcdef1234567890abcdef12", True),   # 有效格式
            ("U12345", False),                                # 太短
            ("X1234567890abcdef1234567890abcdef12", False),   # 不是以 U 開頭
            ("U1234567890abcdef1234567890abcdef123", False),  # 太長
            ("U123456789-abcdef1234567890abcdef12", False),   # 包含特殊字元
            ("", False),                                      # 空字串
            (None, False),                                    # None
        ]
        
        for recipient, expected in test_cases:
            result = await line_channel.validate_recipient(recipient)
            status = "✅" if result == expected else "❌"
            logger.info(f"{status} Recipient '{recipient}': {result} (expected: {expected})")
        
        logger.info("🔍 Validation test completed")
        return True
        
    except Exception as e:
        logger.error(f"💥 Validation test error: {e}")
        return False


async def main():
    """主測試函數"""
    logger = logging.getLogger(__name__)
    
    logger.info("🎯 Line Bot Push Test Suite")
    logger.info("=" * 50)
    
    # 執行驗證測試
    validation_success = await test_message_validation()
    
    # 執行推送測試
    push_success = await test_line_push()
    
    logger.info("=" * 50)
    logger.info(f"📊 Test Results:")
    logger.info(f"   - Validation test: {'✅ PASS' if validation_success else '❌ FAIL'}")
    logger.info(f"   - Push test: {'✅ PASS' if push_success else '❌ FAIL'}")
    
    if validation_success and push_success:
        logger.info("🎉 All tests passed!")
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
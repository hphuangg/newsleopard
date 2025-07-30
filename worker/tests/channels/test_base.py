"""
抽象介面測試

測試 MessageChannel 抽象介面和相關資料結構。
"""

import pytest
import sys
from pathlib import Path

# 添加根目錄到路徑
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from shared.channels import MessageChannel, SendResult, SendStatus, RateLimit


class TestSendResult:
    """SendResult 資料結構測試"""
    
    def test_send_result_success(self):
        """測試成功結果"""
        result = SendResult(
            status=SendStatus.SUCCESS,
            message_id="test_123",
            response_data={"test": "data"}
        )
        
        assert result.is_success() is True
        assert result.is_failed() is False
        assert result.is_rate_limited() is False
        assert result.message_id == "test_123"
        assert result.response_data == {"test": "data"}
    
    def test_send_result_failed(self):
        """測試失敗結果"""
        result = SendResult(
            status=SendStatus.FAILED,
            error_message="Test error"
        )
        
        assert result.is_success() is False
        assert result.is_failed() is True
        assert result.is_rate_limited() is False
        assert result.error_message == "Test error"
    
    def test_send_result_rate_limited(self):
        """測試頻率限制結果"""
        result = SendResult(
            status=SendStatus.RATE_LIMITED,
            error_message="Rate limit exceeded"
        )
        
        assert result.is_success() is False
        assert result.is_failed() is False
        assert result.is_rate_limited() is True
        assert result.error_message == "Rate limit exceeded"


class TestRateLimit:
    """RateLimit 資料結構測試"""
    
    def test_rate_limit_not_exceeded(self):
        """測試未超過限制"""
        rate_limit = RateLimit(
            max_requests=100,
            time_window=3600,
            current_requests=50
        )
        
        assert rate_limit.is_exceeded() is False
        assert rate_limit.remaining_requests() == 50
    
    def test_rate_limit_exceeded(self):
        """測試超過限制"""
        rate_limit = RateLimit(
            max_requests=100,
            time_window=3600,
            current_requests=100
        )
        
        assert rate_limit.is_exceeded() is True
        assert rate_limit.remaining_requests() == 0
    
    def test_rate_limit_over_limit(self):
        """測試超過限制的情況"""
        rate_limit = RateLimit(
            max_requests=100,
            time_window=3600,
            current_requests=150
        )
        
        assert rate_limit.is_exceeded() is True
        assert rate_limit.remaining_requests() == 0  # 不會回傳負數


class MockMessageChannel(MessageChannel):
    """測試用的 Mock MessageChannel"""
    
    def __init__(self, name: str = "mock"):
        self.name = name
        self.available = True
        self.rate_limit_obj = RateLimit(max_requests=100, time_window=3600)
    
    async def send_message(self, content: str, recipient: str) -> SendResult:
        """模擬發送訊息"""
        if not self.available:
            return SendResult(
                status=SendStatus.FAILED, 
                error_message="Channel not available"
            )
        
        if not await self.validate_recipient(recipient):
            return SendResult(
                status=SendStatus.FAILED,
                error_message="Invalid recipient"
            )
        
        return SendResult(
            status=SendStatus.SUCCESS,
            message_id=f"mock_{recipient}_{len(content)}"
        )
    
    async def get_rate_limit(self) -> RateLimit:
        """回傳頻率限制"""
        return self.rate_limit_obj
    
    async def validate_recipient(self, recipient: str) -> bool:
        """驗證收件人"""
        return bool(recipient and len(recipient) > 0)
    
    async def get_channel_name(self) -> str:
        """回傳管道名稱"""
        return self.name
    
    async def is_available(self) -> bool:
        """檢查是否可用"""
        return self.available


class TestMessageChannel:
    """MessageChannel 抽象介面測試"""
    
    @pytest.fixture
    def mock_channel(self):
        """測試用的 Mock Channel"""
        return MockMessageChannel("test_channel")
    
    @pytest.mark.asyncio
    async def test_send_message_success(self, mock_channel):
        """測試成功發送"""
        result = await mock_channel.send_message("Hello", "test_recipient")
        
        assert result.is_success() is True
        assert result.message_id == "mock_test_recipient_5"
    
    @pytest.mark.asyncio
    async def test_send_message_invalid_recipient(self, mock_channel):
        """測試無效收件人"""
        result = await mock_channel.send_message("Hello", "")
        
        assert result.is_failed() is True
        assert "Invalid recipient" in result.error_message
    
    @pytest.mark.asyncio
    async def test_send_message_channel_unavailable(self, mock_channel):
        """測試管道不可用"""
        mock_channel.available = False
        
        result = await mock_channel.send_message("Hello", "test_recipient")
        
        assert result.is_failed() is True
        assert "Channel not available" in result.error_message
    
    @pytest.mark.asyncio
    async def test_get_rate_limit(self, mock_channel):
        """測試取得頻率限制"""
        rate_limit = await mock_channel.get_rate_limit()
        
        assert isinstance(rate_limit, RateLimit)
        assert rate_limit.max_requests == 100
        assert rate_limit.time_window == 3600
    
    @pytest.mark.asyncio
    async def test_validate_recipient(self, mock_channel):
        """測試驗證收件人"""
        assert await mock_channel.validate_recipient("valid_recipient") is True
        assert await mock_channel.validate_recipient("") is False
        assert await mock_channel.validate_recipient(None) is False
    
    @pytest.mark.asyncio
    async def test_get_channel_name(self, mock_channel):
        """測試取得管道名稱"""
        name = await mock_channel.get_channel_name()
        assert name == "test_channel"
    
    @pytest.mark.asyncio
    async def test_is_available(self, mock_channel):
        """測試檢查可用性"""
        assert await mock_channel.is_available() is True
        
        mock_channel.available = False
        assert await mock_channel.is_available() is False
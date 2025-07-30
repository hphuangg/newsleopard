"""
發送管道抽象介面

定義所有發送管道必須實作的介面和資料結構。
"""

from abc import ABC, abstractmethod
from typing import Dict, Optional
from dataclasses import dataclass
from enum import Enum


class SendStatus(Enum):
    """發送狀態枚舉"""
    SUCCESS = "success"
    FAILED = "failed"
    PENDING = "pending"
    RATE_LIMITED = "rate_limited"


@dataclass
class SendResult:
    """發送結果資料結構"""
    status: SendStatus
    message_id: Optional[str] = None
    error_message: Optional[str] = None
    response_data: Optional[Dict] = None
    
    def is_success(self) -> bool:
        """檢查是否發送成功"""
        return self.status == SendStatus.SUCCESS
    
    def is_failed(self) -> bool:
        """檢查是否發送失敗"""
        return self.status == SendStatus.FAILED
    
    def is_rate_limited(self) -> bool:
        """檢查是否被頻率限制"""
        return self.status == SendStatus.RATE_LIMITED


@dataclass
class RateLimit:
    """頻率限制資料結構"""
    max_requests: int
    time_window: int  # 秒
    current_requests: int = 0
    reset_time: Optional[int] = None
    
    def is_exceeded(self) -> bool:
        """檢查是否超過頻率限制"""
        return self.current_requests >= self.max_requests
    
    def remaining_requests(self) -> int:
        """取得剩餘請求數"""
        return max(0, self.max_requests - self.current_requests)


class MessageChannel(ABC):
    """發送管道抽象介面
    
    所有發送管道都必須實作此介面，確保一致的使用方式。
    """
    
    @abstractmethod
    async def send_message(self, content: str, recipient: str) -> SendResult:
        """發送訊息
        
        Args:
            content: 訊息內容
            recipient: 收件人識別碼
            
        Returns:
            SendResult: 發送結果
        """
        pass
    
    @abstractmethod
    async def get_rate_limit(self) -> RateLimit:
        """取得管道頻率限制資訊
        
        Returns:
            RateLimit: 頻率限制資訊
        """
        pass
    
    @abstractmethod
    async def validate_recipient(self, recipient: str) -> bool:
        """驗證收件人格式是否正確
        
        Args:
            recipient: 收件人識別碼
            
        Returns:
            bool: 是否有效
        """
        pass
    
    @abstractmethod
    async def get_channel_name(self) -> str:
        """取得管道名稱
        
        Returns:
            str: 管道名稱
        """
        pass
    
    @abstractmethod
    async def is_available(self) -> bool:
        """檢查管道是否可用
        
        Returns:
            bool: 管道是否可用
        """
        pass
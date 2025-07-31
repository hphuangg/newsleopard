"""
Line Bot 發送管道實作

實作 Line Bot 的具體發送邏輯，包含頻率限制、錯誤處理等。
"""

import asyncio
import logging
import time
from typing import Dict, Optional
import sys
from pathlib import Path

# 添加根目錄到路徑以使用 shared 模組
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from linebot.v3.messaging import (
    AsyncApiClient, 
    AsyncMessagingApi, 
    Configuration,
    TextMessage, 
    PushMessageRequest,
    ApiException
)

from shared.channels import MessageChannel, SendResult, SendStatus, RateLimit
from shared.channels.exceptions import ChannelConfigurationError
from shared.config.settings import settings

logger = logging.getLogger(__name__)


class LineBotChannel(MessageChannel):
    """Line Bot 發送管道實作"""
    
    def __init__(self, channel_access_token: Optional[str] = None):
        """初始化 Line Bot 管道
        
        Args:
            channel_access_token: Line Bot Channel Access Token
        """
        self.channel_access_token = channel_access_token or settings.line_bot.channel_access_token
        
        if not self.channel_access_token:
            raise ChannelConfigurationError("Line Bot Channel Access Token is required")
        
        # 設定 Line Bot API
        configuration = Configuration(access_token=self.channel_access_token)
        async_api_client = AsyncApiClient(configuration)
        self.line_bot_api = AsyncMessagingApi(async_api_client)
        
        logger.info(f"Line Bot API client initialized with timeout: {settings.line_bot.timeout}s")
        
        # 初始化頻率限制
        self.rate_limit = RateLimit(
            max_requests=settings.line_bot.rate_limit_max_requests,
            time_window=settings.line_bot.rate_limit_time_window
        )
        
        # 頻率限制狀態追蹤 (簡單實作，生產環境建議使用 Redis)
        self._rate_limit_start_time = time.time()
        
        logger.info(f"LineBotChannel initialized with rate limit: {self.rate_limit.max_requests}/{self.rate_limit.time_window}s")
    
    async def send_message(self, content: str, recipient: str) -> SendResult:
        """發送 Line Bot 訊息
        
        Args:
            content: 訊息內容
            recipient: Line 用戶 ID
            
        Returns:
            SendResult: 發送結果
        """
        try:
            # 檢查頻率限制
            if not await self._check_rate_limit():
                logger.warning(f"Rate limit exceeded for Line Bot channel")
                return SendResult(
                    status=SendStatus.RATE_LIMITED,
                    error_message="Rate limit exceeded"
                )
            
            # 驗證收件人
            if not await self.validate_recipient(recipient):
                logger.error(f"Invalid Line Bot recipient: {recipient}")
                return SendResult(
                    status=SendStatus.FAILED,
                    error_message="Invalid recipient format"
                )
            
            # 準備發送訊息
            message = TextMessage(text=content)
            push_message_request = PushMessageRequest(
                to=recipient,
                messages=[message]
            )
            
            logger.info(f"Sending Line Bot message to {recipient}")
            
            # 發送訊息 (添加超時處理)
            try:
                import asyncio
                logger.info(f"🔄 Starting Line Bot API call with timeout: {settings.line_bot.timeout}s")
                start_time = asyncio.get_event_loop().time()
                
                response = await asyncio.wait_for(
                    self.line_bot_api.push_message(push_message_request=push_message_request),
                    timeout=float(settings.line_bot.timeout)  # 使用設定中的超時時間
                )
                
                end_time = asyncio.get_event_loop().time()
                duration = end_time - start_time
                logger.info(f"✅ Line Bot API call completed in {duration:.2f}s")
                logger.info(f"Sending Line Bot message to {recipient} completed. response: {response}")
                
            except asyncio.TimeoutError:
                logger.error(f"❌ Line Bot API call timed out after 10s for recipient {recipient}")
                return SendResult(
                    status=SendStatus.FAILED,
                    error_message="Line Bot API call timed out after 10s"
                )
            
            # 更新頻率限制
            await self._update_rate_limit()
            
            logger.info(f"Line Bot message sent successfully to {recipient}")
            return SendResult(
                status=SendStatus.SUCCESS,
                message_id=response.get('requestId') if hasattr(response, 'get') else None,
                response_data={'response': str(response)} if response else None
            )
            
        except ApiException as e:
            logger.error(f"Line Bot API error: {e}")
            return SendResult(
                status=SendStatus.FAILED,
                error_message=f"Line Bot API error: {e.message if hasattr(e, 'message') else str(e)}"
            )
        except Exception as e:
            logger.error(f"Unexpected error in Line Bot send_message: {e}")
            return SendResult(
                status=SendStatus.FAILED,
                error_message=f"Unexpected error: {str(e)}"
            )
    
    async def get_rate_limit(self) -> RateLimit:
        """取得 Line Bot 頻率限制資訊
        
        Returns:
            RateLimit: 頻率限制資訊
        """
        # 檢查是否需要重置計數器
        current_time = time.time()
        if current_time - self._rate_limit_start_time >= self.rate_limit.time_window:
            self.rate_limit.current_requests = 0
            self._rate_limit_start_time = current_time
            self.rate_limit.reset_time = int(current_time + self.rate_limit.time_window)
        
        return self.rate_limit
    
    async def validate_recipient(self, recipient: str) -> bool:
        """驗證 Line 用戶 ID 格式
        
        Args:
            recipient: Line 用戶 ID
            
        Returns:
            bool: 是否有效
        """
        try:
            logger.info(f"🔍 Validating Line Bot recipient: {recipient}")
            
            # 檢查基本格式 - Line 用戶 ID 通常以 'U' 開頭，長度約 33 字元
            if not recipient or not isinstance(recipient, str):
                logger.error(f"Recipient is empty or not a string: {recipient}")
                return False
            
            if not recipient.startswith('U'):
                logger.error(f"Recipient does not start with 'U': {recipient}")
                return False
            
            # if len(recipient) != 33:
            #     return False
            
            # 檢查是否只包含英數字
            if not recipient[1:].isalnum():
                logger.error(f"Recipient contains non-alphanumeric characters: {recipient}")
                return False
            
            logger.info(f"✅ Recipient validation passed: {recipient}")
            return True
            
        except Exception as e:
            logger.error(f"Error validating Line Bot recipient {recipient}: {e}")
            return False
    
    async def get_channel_name(self) -> str:
        """取得管道名稱
        
        Returns:
            str: 管道名稱
        """
        return "line"
    
    async def is_available(self) -> bool:
        """檢查 Line Bot 管道是否可用
        
        Returns:
            bool: 管道是否可用
        """
        try:
            logger.info(f"🔍 Checking Line Bot availability...")
            logger.debug(f"Channel access token length: {len(self.channel_access_token) if self.channel_access_token else 0}")
            
            # 檢查是否有 token
            if not self.channel_access_token:
                logger.error("Line Bot channel access token is not set")
                return False
            
            # 可以嘗試調用 API 來檢查 token 是否有效
            # 這裡先簡單檢查 token 格式
            if len(self.channel_access_token) < 100:  # Line Bot token 通常很長
                logger.error(f"Line Bot channel access token seems invalid (length: {len(self.channel_access_token)})")
                return False
            
            # 嘗試測試 API 連接 (可選，但會增加檢查時間)
            try:
                import asyncio
                # 這裡可以添加一個簡單的 API 測試調用
                # 例如獲取 bot 資訊等
                logger.info("Testing Line Bot API connection...")
                # 暫時跳過實際 API 測試，只檢查 token 格式
                
            except Exception as api_test_error:
                logger.warning(f"Line Bot API test failed: {api_test_error}")
                # 不因為 API 測試失敗而返回 False，因為可能是網路問題
            
            logger.info("✅ Line Bot channel is available")
            return True
            
        except Exception as e:
            logger.error(f"Error checking Line Bot availability: {e}")
            return False
    
    async def _check_rate_limit(self) -> bool:
        """檢查頻率限制
        
        Returns:
            bool: 是否在限制內
        """
        rate_limit = await self.get_rate_limit()
        return not rate_limit.is_exceeded()
    
    async def _update_rate_limit(self):
        """更新頻率限制計數"""
        self.rate_limit.current_requests += 1
        logger.debug(f"Rate limit updated: {self.rate_limit.current_requests}/{self.rate_limit.max_requests}")
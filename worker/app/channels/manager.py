"""
管道管理器

統一管理所有發送管道的初始化、健康檢查和訊息發送。
"""

import logging
import asyncio
import sys
from pathlib import Path
from typing import Dict, List, Optional

# 添加根目錄到路徑以使用 shared 模組
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from shared.channels import MessageChannel, SendResult, SendStatus
from shared.channels.exceptions import ChannelNotFoundError, ChannelUnavailableError
from .factory import ChannelFactory

logger = logging.getLogger(__name__)


class ChannelManager:
    """管道管理器
    
    統一管理和操作所有發送管道。
    """
    
    def __init__(self):
        """初始化管道管理器"""
        self.factory = ChannelFactory()
        self._active_channels: Dict[str, MessageChannel] = {}
        self._channel_health_status: Dict[str, bool] = {}
        
        logger.info("ChannelManager initializing...")
        
        # 異步初始化管道 (需要在異步環境中調用)
        # asyncio.create_task(self._initialize_channels())
    
    async def initialize_channels(self):
        """初始化所有管道 (需要在異步環境中調用)"""
        available_channels = self.factory.get_available_channels()
        
        logger.info(f"Initializing channels: {available_channels}")
        
        for channel_type in available_channels:
            try:
                config = self.factory.get_channel_config(channel_type)
                
                # 檢查是否有必要的配置
                if not self._has_required_config(channel_type, config):
                    logger.warning(f"Channel {channel_type} missing required configuration, skipping")
                    continue
                
                channel = self.factory.create_channel(channel_type, **config)
                
                # 檢查管道是否可用
                if await channel.is_available():
                    self._active_channels[channel_type] = channel
                    self._channel_health_status[channel_type] = True
                    logger.info(f"Channel {channel_type} initialized and available")
                else:
                    self._channel_health_status[channel_type] = False
                    logger.warning(f"Channel {channel_type} initialized but not available")
                    
            except Exception as e:
                logger.error(f"Failed to initialize channel {channel_type}: {e}")
                self._channel_health_status[channel_type] = False
        
        logger.info(f"Channel initialization completed. Active channels: {list(self._active_channels.keys())}")
    
    def _has_required_config(self, channel_type: str, config: Dict) -> bool:
        """檢查管道是否有必要的配置
        
        Args:
            channel_type: 管道類型
            config: 配置字典
            
        Returns:
            bool: 是否有必要配置
        """
        required_configs = {
            "line": ["channel_access_token"],
            "sms": ["api_key"],
            "email": ["smtp_host", "smtp_username", "smtp_password"]
        }
        
        required_keys = required_configs.get(channel_type, [])
        
        for key in required_keys:
            if not config.get(key):
                return False
        
        return True
    
    async def send_message(self, channel_type: str, content: str, recipient: str) -> SendResult:
        """透過指定管道發送訊息
        
        Args:
            channel_type: 管道類型
            content: 訊息內容
            recipient: 收件人
            
        Returns:
            SendResult: 發送結果
        """
        try:
            if channel_type not in self._active_channels:
                logger.error(f"Channel {channel_type} not available")
                return SendResult(
                    status=SendStatus.FAILED,
                    error_message=f"Channel {channel_type} not available"
                )
            
            channel = self._active_channels[channel_type]
            
            # 檢查管道健康狀態
            if not self._channel_health_status.get(channel_type, False):
                logger.warning(f"Channel {channel_type} is unhealthy, attempting to send anyway")
            
            logger.info(f"Sending message via {channel_type} to {recipient}")
            result = await channel.send_message(content, recipient)
            
            # 更新健康狀態
            self._channel_health_status[channel_type] = result.is_success()
            
            return result
            
        except Exception as e:
            logger.error(f"Error sending message via {channel_type}: {e}")
            # 標記管道為不健康
            self._channel_health_status[channel_type] = False
            
            return SendResult(
                status=SendStatus.FAILED,
                error_message=f"Error sending message: {str(e)}"
            )
    
    async def send_message_multi_channel(
        self, 
        channels: List[str], 
        content: str, 
        recipients: Dict[str, str]
    ) -> Dict[str, SendResult]:
        """透過多個管道發送訊息
        
        Args:
            channels: 管道類型列表
            content: 訊息內容
            recipients: 管道對應的收件人 {channel_type: recipient}
            
        Returns:
            Dict[str, SendResult]: 各管道的發送結果
        """
        results = {}
        
        # 建立並發送送任務
        tasks = []
        for channel_type in channels:
            if channel_type in recipients:
                recipient = recipients[channel_type]
                task = asyncio.create_task(
                    self.send_message(channel_type, content, recipient),
                    name=f"send_{channel_type}"
                )
                tasks.append((channel_type, task))
        
        # 等待所有任務完成
        for channel_type, task in tasks:
            try:
                result = await task
                results[channel_type] = result
            except Exception as e:
                logger.error(f"Error in multi-channel send for {channel_type}: {e}")
                results[channel_type] = SendResult(
                    status=SendStatus.FAILED,
                    error_message=f"Multi-channel send error: {str(e)}"
                )
        
        return results
    
    def get_available_channels(self) -> List[str]:
        """取得可用的管道列表
        
        Returns:
            List[str]: 可用管道列表
        """
        return list(self._active_channels.keys())
    
    def get_all_registered_channels(self) -> List[str]:
        """取得所有註冊的管道列表 (包含不可用的)
        
        Returns:
            List[str]: 所有註冊管道列表
        """
        return self.factory.get_available_channels()
    
    async def get_channel_status(self, channel_type: str) -> Dict:
        """取得管道狀態資訊
        
        Args:
            channel_type: 管道類型
            
        Returns:
            Dict: 管道狀態資訊
        """
        if channel_type not in self._active_channels:
            return {
                "available": False, 
                "error": "Channel not found or not initialized",
                "health_status": self._channel_health_status.get(channel_type, False)
            }
        
        try:
            channel = self._active_channels[channel_type]
            rate_limit = await channel.get_rate_limit()
            is_available = await channel.is_available()
            
            return {
                "available": is_available,
                "health_status": self._channel_health_status.get(channel_type, False),
                "rate_limit": {
                    "max_requests": rate_limit.max_requests,
                    "time_window": rate_limit.time_window,
                    "current_requests": rate_limit.current_requests,
                    "remaining_requests": rate_limit.remaining_requests(),
                    "reset_time": rate_limit.reset_time
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting status for channel {channel_type}: {e}")
            return {
                "available": False,
                "error": str(e),
                "health_status": False
            }
    
    async def get_all_channels_status(self) -> Dict[str, Dict]:
        """取得所有管道的狀態資訊
        
        Returns:
            Dict[str, Dict]: 所有管道狀態資訊
        """
        status = {}
        all_channels = self.get_all_registered_channels()
        
        for channel_type in all_channels:
            status[channel_type] = await self.get_channel_status(channel_type)
        
        return status
    
    async def health_check(self) -> Dict[str, bool]:
        """執行所有管道的健康檢查
        
        Returns:
            Dict[str, bool]: 各管道健康狀態
        """
        health_status = {}
        
        for channel_type, channel in self._active_channels.items():
            try:
                is_healthy = await channel.is_available()
                health_status[channel_type] = is_healthy
                self._channel_health_status[channel_type] = is_healthy
                
                if is_healthy:
                    logger.debug(f"Channel {channel_type} health check: OK")
                else:
                    logger.warning(f"Channel {channel_type} health check: FAILED")
                    
            except Exception as e:
                logger.error(f"Health check failed for {channel_type}: {e}")
                health_status[channel_type] = False
                self._channel_health_status[channel_type] = False
        
        return health_status
    
    async def refresh_channel(self, channel_type: str) -> bool:
        """重新初始化指定管道
        
        Args:
            channel_type: 管道類型
            
        Returns:
            bool: 是否成功重新初始化
        """
        try:
            logger.info(f"Refreshing channel: {channel_type}")
            
            # 移除舊實例
            if channel_type in self._active_channels:
                del self._active_channels[channel_type]
            
            # 重新建立實例
            config = self.factory.get_channel_config(channel_type)
            if not self._has_required_config(channel_type, config):
                logger.error(f"Channel {channel_type} missing required configuration")
                return False
            
            channel = self.factory.create_channel(channel_type, **config)
            
            if await channel.is_available():
                self._active_channels[channel_type] = channel
                self._channel_health_status[channel_type] = True
                logger.info(f"Channel {channel_type} refreshed successfully")
                return True
            else:
                self._channel_health_status[channel_type] = False
                logger.warning(f"Channel {channel_type} refreshed but not available")
                return False
                
        except Exception as e:
            logger.error(f"Failed to refresh channel {channel_type}: {e}")
            self._channel_health_status[channel_type] = False
            return False
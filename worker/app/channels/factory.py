"""
管道工廠模式實作

使用工廠模式建立和管理不同類型的發送管道。
"""

import logging
import sys
from pathlib import Path
from typing import Dict, Type, Any

# 添加根目錄到路徑以使用 shared 模組
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from shared.channels import MessageChannel
from shared.channels.exceptions import ChannelNotFoundError, ChannelConfigurationError
from shared.config.settings import settings
from .line_bot import LineBotChannel

logger = logging.getLogger(__name__)


class ChannelFactory:
    """管道工廠類別
    
    使用工廠模式管理各種發送管道的建立和配置。
    """
    
    def __init__(self):
        """初始化工廠"""
        self._channels: Dict[str, Type[MessageChannel]] = {}
        self._instances: Dict[str, MessageChannel] = {}
        self._register_default_channels()
        
        logger.info("ChannelFactory initialized")
    
    def _register_default_channels(self):
        """註冊預設管道類型"""
        self.register_channel("line", LineBotChannel)
        # 未來可以註冊更多管道
        # self.register_channel("sms", SMSChannel)
        # self.register_channel("email", EmailChannel)
        
        logger.info(f"Registered default channels: {list(self._channels.keys())}")
    
    def register_channel(self, channel_type: str, channel_class: Type[MessageChannel]):
        """註冊新的管道類型
        
        Args:
            channel_type: 管道類型名稱
            channel_class: 管道類別
        """
        if not issubclass(channel_class, MessageChannel):
            raise ValueError(f"Channel class must inherit from MessageChannel")
        
        self._channels[channel_type] = channel_class
        logger.info(f"Registered channel type: {channel_type}")
    
    def create_channel(self, channel_type: str, **kwargs) -> MessageChannel:
        """建立管道實例
        
        Args:
            channel_type: 管道類型
            **kwargs: 管道建立參數
            
        Returns:
            MessageChannel: 管道實例
            
        Raises:
            ChannelNotFoundError: 管道類型不存在
            ChannelConfigurationError: 管道配置錯誤
        """
        if channel_type not in self._channels:
            raise ChannelNotFoundError(f"Unsupported channel type: {channel_type}")
        
        # 生成實例鍵值
        instance_key = f"{channel_type}_{hash(str(sorted(kwargs.items())))}"
        
        # 檢查是否已有實例 (單例模式)
        if instance_key in self._instances:
            logger.debug(f"Returning existing instance for {channel_type}")
            return self._instances[instance_key]
        
        try:
            # 建立新實例
            channel_class = self._channels[channel_type]
            
            # 如果沒有提供參數，使用預設配置
            if not kwargs:
                kwargs = self.get_channel_config(channel_type)
            
            instance = channel_class(**kwargs)
            self._instances[instance_key] = instance
            
            logger.info(f"Created new channel instance: {channel_type}")
            return instance
            
        except Exception as e:
            logger.error(f"Failed to create channel {channel_type}: {e}")
            raise ChannelConfigurationError(f"Failed to create channel {channel_type}: {e}")
    
    def get_available_channels(self) -> list[str]:
        """取得可用的管道類型列表
        
        Returns:
            list[str]: 可用管道類型
        """
        return list(self._channels.keys())
    
    def get_channel_config(self, channel_type: str) -> Dict[str, Any]:
        """取得管道預設配置
        
        Args:
            channel_type: 管道類型
            
        Returns:
            Dict[str, Any]: 管道配置
        """
        configs = {
            "line": {
                "channel_access_token": settings.line_bot.channel_access_token,
            },
            "sms": {
                "api_key": settings.channels.sms_api_key,
            },
            "email": {
                "smtp_host": settings.channels.smtp_host,
                "smtp_port": settings.channels.smtp_port,
                "smtp_username": settings.channels.smtp_username,
                "smtp_password": settings.channels.smtp_password,
            }
        }
        
        return configs.get(channel_type, {})
    
    def get_channel_rate_limit_config(self, channel_type: str) -> Dict[str, int]:
        """取得管道頻率限制配置
        
        Args:
            channel_type: 管道類型
            
        Returns:
            Dict[str, int]: 頻率限制配置
        """
        rate_limit_configs = {
            "line": {
                "max_requests": settings.line_bot.rate_limit_max_requests,
                "time_window": settings.line_bot.rate_limit_time_window
            },
            "sms": {
                "max_requests": settings.channels.sms_rate_limit_max_requests,
                "time_window": settings.channels.sms_rate_limit_time_window
            },
            "email": {
                "max_requests": settings.channels.email_rate_limit_max_requests,
                "time_window": settings.channels.email_rate_limit_time_window
            }
        }
        
        return rate_limit_configs.get(channel_type, {"max_requests": 100, "time_window": 3600})
    
    def clear_instances(self):
        """清除所有管道實例 (主要用於測試)"""
        self._instances.clear()
        logger.info("Cleared all channel instances")
    
    def get_instance_count(self) -> int:
        """取得目前實例數量 (主要用於測試)"""
        return len(self._instances)
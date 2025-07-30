"""
管道工廠模式測試

測試 ChannelFactory 的功能。
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# 添加根目錄到路徑
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from shared.channels import MessageChannel
from shared.channels.exceptions import ChannelNotFoundError, ChannelConfigurationError
from worker.app.channels.factory import ChannelFactory
from worker.tests.channels.test_base import MockMessageChannel


class AnotherMockChannel(MessageChannel):
    """另一個測試用的 Mock Channel"""
    
    async def send_message(self, content: str, recipient: str):
        return None
    
    async def get_rate_limit(self):
        return None
    
    async def validate_recipient(self, recipient: str) -> bool:
        return True
    
    async def get_channel_name(self) -> str:
        return "another_mock"
    
    async def is_available(self) -> bool:
        return True


class TestChannelFactory:
    """ChannelFactory 測試"""
    
    @pytest.fixture
    def factory(self):
        """測試用的工廠實例"""
        factory = ChannelFactory()
        factory.clear_instances()  # 清除任何現有實例
        return factory
    
    def test_factory_initialization(self, factory):
        """測試工廠初始化"""
        available_channels = factory.get_available_channels()
        assert "line" in available_channels
        assert len(available_channels) > 0
    
    def test_register_channel(self, factory):
        """測試註冊管道"""
        factory.register_channel("test_mock", MockMessageChannel)
        
        available_channels = factory.get_available_channels()
        assert "test_mock" in available_channels
    
    def test_register_invalid_channel(self, factory):
        """測試註冊無效管道"""
        with pytest.raises(ValueError, match="Channel class must inherit from MessageChannel"):
            factory.register_channel("invalid", str)  # str 不是 MessageChannel 的子類別
    
    @patch('worker.app.channels.factory.settings')
    def test_create_channel_with_config(self, mock_settings, factory):
        """測試使用配置建立管道"""
        # Mock settings
        mock_settings.line_bot.channel_access_token = "test_token"
        
        factory.register_channel("test_mock", MockMessageChannel)
        
        # 測試使用預設配置
        channel = factory.create_channel("test_mock")
        assert isinstance(channel, MockMessageChannel)
    
    def test_create_channel_with_params(self, factory):
        """測試使用參數建立管道"""
        factory.register_channel("test_mock", MockMessageChannel)
        
        channel = factory.create_channel("test_mock", name="custom_name")
        assert isinstance(channel, MockMessageChannel)
        assert channel.name == "custom_name"
    
    def test_create_channel_singleton(self, factory):
        """測試管道單例模式"""
        factory.register_channel("test_mock", MockMessageChannel)
        
        channel1 = factory.create_channel("test_mock", name="same_config")
        channel2 = factory.create_channel("test_mock", name="same_config")
        
        # 相同配置應該回傳相同實例
        assert channel1 is channel2
    
    def test_create_channel_different_configs(self, factory):
        """測試不同配置建立不同實例"""
        factory.register_channel("test_mock", MockMessageChannel)
        
        channel1 = factory.create_channel("test_mock", name="config1")
        channel2 = factory.create_channel("test_mock", name="config2")
        
        # 不同配置應該回傳不同實例
        assert channel1 is not channel2
        assert channel1.name == "config1"
        assert channel2.name == "config2"
    
    def test_create_channel_not_found(self, factory):
        """測試建立不存在的管道"""
        with pytest.raises(ChannelNotFoundError, match="Unsupported channel type: nonexistent"):
            factory.create_channel("nonexistent")
    
    def test_create_channel_configuration_error(self, factory):
        """測試管道配置錯誤"""
        # 註冊一個會拋出例外的管道類別
        class ErrorChannel(MessageChannel):
            def __init__(self, **kwargs):
                raise ValueError("Configuration error")
            
            async def send_message(self, content: str, recipient: str):
                pass
            async def get_rate_limit(self):
                pass
            async def validate_recipient(self, recipient: str) -> bool:
                pass
            async def get_channel_name(self) -> str:
                pass
            async def is_available(self) -> bool:
                pass
        
        factory.register_channel("error_channel", ErrorChannel)
        
        with pytest.raises(ChannelConfigurationError):
            factory.create_channel("error_channel")
    
    @patch('worker.app.channels.factory.settings')
    def test_get_channel_config(self, mock_settings, factory):
        """測試取得管道配置"""
        # Mock settings
        mock_settings.line_bot.channel_access_token = "test_line_token"
        mock_settings.channels.sms_api_key = "test_sms_key"
        mock_settings.channels.smtp_host = "test_smtp_host"
        mock_settings.channels.smtp_port = 587
        mock_settings.channels.smtp_username = "test_user"
        mock_settings.channels.smtp_password = "test_pass"
        
        # 測試 Line 配置
        line_config = factory.get_channel_config("line")
        assert line_config["channel_access_token"] == "test_line_token"
        
        # 測試 SMS 配置
        sms_config = factory.get_channel_config("sms")
        assert sms_config["api_key"] == "test_sms_key"
        
        # 測試 Email 配置
        email_config = factory.get_channel_config("email")
        assert email_config["smtp_host"] == "test_smtp_host"
        assert email_config["smtp_port"] == 587
        
        # 測試不存在的管道
        unknown_config = factory.get_channel_config("unknown")
        assert unknown_config == {}
    
    @patch('worker.app.channels.factory.settings')
    def test_get_channel_rate_limit_config(self, mock_settings, factory):
        """測試取得管道頻率限制配置"""
        # Mock settings
        mock_settings.line_bot.rate_limit_max_requests = 1000
        mock_settings.line_bot.rate_limit_time_window = 3600
        mock_settings.channels.sms_rate_limit_max_requests = 100
        mock_settings.channels.sms_rate_limit_time_window = 3600
        
        # 測試 Line 頻率限制配置
        line_rate_config = factory.get_channel_rate_limit_config("line")
        assert line_rate_config["max_requests"] == 1000
        assert line_rate_config["time_window"] == 3600
        
        # 測試 SMS 頻率限制配置
        sms_rate_config = factory.get_channel_rate_limit_config("sms")
        assert sms_rate_config["max_requests"] == 100
        
        # 測試預設值
        unknown_rate_config = factory.get_channel_rate_limit_config("unknown")
        assert unknown_rate_config["max_requests"] == 100
        assert unknown_rate_config["time_window"] == 3600
    
    def test_clear_instances(self, factory):
        """測試清除實例"""
        factory.register_channel("test_mock", MockMessageChannel)
        
        # 建立一些實例
        factory.create_channel("test_mock", name="test1")
        factory.create_channel("test_mock", name="test2")
        
        assert factory.get_instance_count() == 2
        
        # 清除實例
        factory.clear_instances()
        assert factory.get_instance_count() == 0
        
        # 重新建立實例應該是新的
        new_channel = factory.create_channel("test_mock", name="test1")
        assert factory.get_instance_count() == 1
"""
管道管理器測試

測試 ChannelManager 的功能。
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock

# 添加根目錄到路徑
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from shared.channels import SendResult, SendStatus, RateLimit
from worker.app.channels.manager import ChannelManager
from worker.tests.channels.test_base import MockMessageChannel


class TestChannelManager:
    """ChannelManager 測試"""
    
    @pytest.fixture
    def manager(self):
        """測試用的管理器實例"""
        return ChannelManager()
    
    @pytest.fixture
    def mock_factory(self):
        """Mock ChannelFactory"""
        factory = MagicMock()
        factory.get_available_channels.return_value = ["test_channel"]
        factory.get_channel_config.return_value = {"name": "test"}
        factory.create_channel.return_value = MockMessageChannel("test")
        return factory
    
    def test_manager_initialization(self, manager):
        """測試管理器初始化"""
        assert manager.factory is not None
        assert isinstance(manager._active_channels, dict)
        assert isinstance(manager._channel_health_status, dict)
    
    @patch('worker.app.channels.manager.ChannelFactory')
    @pytest.mark.asyncio
    async def test_initialize_channels_success(self, mock_factory_class):
        """測試成功初始化管道"""
        # 設定 Mock
        mock_factory = MagicMock()
        mock_factory.get_available_channels.return_value = ["test_channel"]
        mock_factory.get_channel_config.return_value = {"name": "test"}
        
        mock_channel = MockMessageChannel("test")
        mock_channel.available = True
        mock_factory.create_channel.return_value = mock_channel
        
        mock_factory_class.return_value = mock_factory
        
        # 建立管理器並初始化
        manager = ChannelManager()
        await manager.initialize_channels()
        
        # 驗證結果
        assert "test_channel" in manager._active_channels
        assert manager._channel_health_status["test_channel"] is True
    
    @patch('worker.app.channels.manager.ChannelFactory')
    @pytest.mark.asyncio
    async def test_initialize_channels_unavailable(self, mock_factory_class):
        """測試初始化不可用的管道"""
        # 設定 Mock
        mock_factory = MagicMock()
        mock_factory.get_available_channels.return_value = ["test_channel"]
        mock_factory.get_channel_config.return_value = {"name": "test"}
        
        mock_channel = MockMessageChannel("test")
        mock_channel.available = False  # 設定為不可用
        mock_factory.create_channel.return_value = mock_channel
        
        mock_factory_class.return_value = mock_factory
        
        # 建立管理器並初始化
        manager = ChannelManager()
        await manager.initialize_channels()
        
        # 驗證結果
        assert "test_channel" not in manager._active_channels
        assert manager._channel_health_status["test_channel"] is False
    
    @patch('worker.app.channels.manager.ChannelFactory')
    @pytest.mark.asyncio
    async def test_initialize_channels_missing_config(self, mock_factory_class):
        """測試缺少配置的管道初始化"""
        # 設定 Mock
        mock_factory = MagicMock()
        mock_factory.get_available_channels.return_value = ["line"]
        mock_factory.get_channel_config.return_value = {"channel_access_token": ""}  # 空的必要配置
        
        mock_factory_class.return_value = mock_factory
        
        # 建立管理器並初始化
        manager = ChannelManager()
        await manager.initialize_channels()
        
        # 驗證結果：缺少配置的管道不應該被初始化
        assert "line" not in manager._active_channels
    
    @pytest.mark.asyncio
    async def test_send_message_success(self):
        """測試成功發送訊息"""
        manager = ChannelManager()
        
        # 手動添加一個測試管道
        mock_channel = MockMessageChannel("test")
        manager._active_channels["test_channel"] = mock_channel
        manager._channel_health_status["test_channel"] = True
        
        # 發送訊息
        result = await manager.send_message("test_channel", "Hello", "recipient")
        
        assert result.is_success() is True
        assert result.message_id == "mock_recipient_5"
    
    @pytest.mark.asyncio
    async def test_send_message_channel_not_available(self):
        """測試發送到不可用的管道"""
        manager = ChannelManager()
        
        # 發送到不存在的管道
        result = await manager.send_message("nonexistent", "Hello", "recipient")
        
        assert result.is_failed() is True
        assert "not available" in result.error_message
    
    @pytest.mark.asyncio
    async def test_send_message_multi_channel(self):
        """測試多管道發送"""
        manager = ChannelManager()
        
        # 添加多個測試管道
        mock_channel1 = MockMessageChannel("test1")
        mock_channel2 = MockMessageChannel("test2")
        
        manager._active_channels["channel1"] = mock_channel1
        manager._active_channels["channel2"] = mock_channel2
        manager._channel_health_status["channel1"] = True
        manager._channel_health_status["channel2"] = True
        
        # 多管道發送
        results = await manager.send_message_multi_channel(
            channels=["channel1", "channel2"],
            content="Hello",
            recipients={"channel1": "recipient1", "channel2": "recipient2"}
        )
        
        assert len(results) == 2
        assert results["channel1"].is_success() is True
        assert results["channel2"].is_success() is True
    
    def test_get_available_channels(self):
        """測試取得可用管道列表"""
        manager = ChannelManager()
        
        # 添加測試管道
        manager._active_channels["test1"] = MockMessageChannel("test1")
        manager._active_channels["test2"] = MockMessageChannel("test2")
        
        available_channels = manager.get_available_channels()
        assert "test1" in available_channels
        assert "test2" in available_channels
        assert len(available_channels) == 2
    
    @pytest.mark.asyncio
    async def test_get_channel_status_success(self):
        """測試取得管道狀態 - 成功"""
        manager = ChannelManager()
        
        # 添加測試管道
        mock_channel = MockMessageChannel("test")
        manager._active_channels["test_channel"] = mock_channel
        manager._channel_health_status["test_channel"] = True
        
        status = await manager.get_channel_status("test_channel")
        
        assert status["available"] is True
        assert status["health_status"] is True
        assert "rate_limit" in status
        assert status["rate_limit"]["max_requests"] == 100
    
    @pytest.mark.asyncio
    async def test_get_channel_status_not_found(self):
        """測試取得不存在管道的狀態"""
        manager = ChannelManager()
        
        status = await manager.get_channel_status("nonexistent")
        
        assert status["available"] is False
        assert "not found" in status["error"]
        assert status["health_status"] is False
    
    @pytest.mark.asyncio
    async def test_get_all_channels_status(self):
        """測試取得所有管道狀態"""
        manager = ChannelManager()
        
        # Mock factory 回傳
        with patch.object(manager.factory, 'get_available_channels', return_value=["test1", "test2"]):
            # 添加一個活躍管道
            manager._active_channels["test1"] = MockMessageChannel("test1")
            manager._channel_health_status["test1"] = True
            
            all_status = await manager.get_all_channels_status()
            
            assert "test1" in all_status
            assert "test2" in all_status
            assert all_status["test1"]["available"] is True
            assert all_status["test2"]["available"] is False
    
    @pytest.mark.asyncio
    async def test_health_check(self):
        """測試健康檢查"""
        manager = ChannelManager()
        
        # 添加測試管道
        mock_channel1 = MockMessageChannel("test1")
        mock_channel1.available = True
        mock_channel2 = MockMessageChannel("test2")
        mock_channel2.available = False
        
        manager._active_channels["channel1"] = mock_channel1
        manager._active_channels["channel2"] = mock_channel2
        
        health_status = await manager.health_check()
        
        assert health_status["channel1"] is True
        assert health_status["channel2"] is False
        assert manager._channel_health_status["channel1"] is True
        assert manager._channel_health_status["channel2"] is False
    
    @pytest.mark.asyncio
    async def test_refresh_channel_success(self):
        """測試成功重新整理管道"""
        manager = ChannelManager()
        
        # Mock factory
        with patch.object(manager.factory, 'get_channel_config', return_value={"name": "refreshed"}):
            with patch.object(manager.factory, 'create_channel') as mock_create:
                mock_channel = MockMessageChannel("refreshed")
                mock_channel.available = True
                mock_create.return_value = mock_channel
                
                # 添加舊管道
                old_channel = MockMessageChannel("old")
                manager._active_channels["test_channel"] = old_channel
                
                # 重新整理
                success = await manager.refresh_channel("test_channel")
                
                assert success is True
                assert manager._active_channels["test_channel"] is not old_channel
                assert manager._channel_health_status["test_channel"] is True
    
    @pytest.mark.asyncio
    async def test_refresh_channel_missing_config(self):
        """測試重新整理缺少配置的管道"""
        manager = ChannelManager()
        
        # Mock factory 回傳空配置
        with patch.object(manager.factory, 'get_channel_config', return_value={}):
            success = await manager.refresh_channel("line")  # line 需要 channel_access_token
            
            assert success is False
            assert manager._channel_health_status.get("line", True) is False
    
    def test_has_required_config(self, manager):
        """測試檢查必要配置"""
        # Line Bot 需要 channel_access_token
        assert manager._has_required_config("line", {"channel_access_token": "token"}) is True
        assert manager._has_required_config("line", {"channel_access_token": ""}) is False
        assert manager._has_required_config("line", {}) is False
        
        # SMS 需要 api_key
        assert manager._has_required_config("sms", {"api_key": "key"}) is True
        assert manager._has_required_config("sms", {"api_key": ""}) is False
        
        # Email 需要 smtp_host, smtp_username, smtp_password
        email_config = {
            "smtp_host": "host",
            "smtp_username": "user", 
            "smtp_password": "pass"
        }
        assert manager._has_required_config("email", email_config) is True
        
        incomplete_email_config = {
            "smtp_host": "host",
            "smtp_username": "",  # 缺少 username
            "smtp_password": "pass"
        }
        assert manager._has_required_config("email", incomplete_email_config) is False
        
        # 未知管道類型應該回傳 True (沒有特殊要求)
        assert manager._has_required_config("unknown", {}) is True
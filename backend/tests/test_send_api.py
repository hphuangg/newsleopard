"""
Send API Tests

發送 API 端點的測試。
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock, AsyncMock
from app.main import app

client = TestClient(app)


class TestSendMessageAPI:
    """發送訊息 API 測試"""
    
    def test_send_message_success(self):
        """測試成功發送訊息"""
        with patch('app.services.send_service.send_service.send_message') as mock_send:
            mock_send.return_value = {
                "success": True,
                "batch_id": "test-batch-id",
                "status": "accepted",
                "total_count": 1,
                "message": "發送請求已接受，正在處理中"
            }
            
            response = client.post(
                "/api/v1/send/send-message",
                json={
                    "content": "測試訊息",
                    "channel": "line",
                    "recipients": [
                        {"id": "user_123", "type": "line"}
                    ]
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] == True
            assert data["batch_id"] == "test-batch-id"
    
    def test_send_message_validation_error(self):
        """測試驗證錯誤"""
        response = client.post(
            "/api/v1/send/send-message",
            json={
                "content": "",
                "channel": "invalid_channel",
                "recipients": []
            }
        )
        
        assert response.status_code == 422
    

    def test_send_message_invalid_channel(self):
        """測試無效管道"""
        response = client.post(
            "/api/v1/send/send-message",
            json={
                "content": "測試訊息",
                "channel": "invalid_channel",
                "recipients": [
                    {"id": "user_123", "type": "line"}
                ]
            }
        )
        
        assert response.status_code == 422



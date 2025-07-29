"""
SQS 佇列系統測試

測試 AWS SQS 整合功能，包含佇列管理、Worker 處理和發送服務整合。
"""

import pytest
import asyncio
import json
from unittest.mock import Mock, patch, AsyncMock
from uuid import uuid4

from app.services.sqs_queue_manager import SQSQueueManager
from app.services.send_service import SendService
from app.workers.sqs_worker import SQSWorker


class TestSQSQueueManager:
    """測試 SQS 佇列管理器"""
    
    @pytest.fixture
    def mock_sqs_client(self):
        """模擬 SQS 客戶端"""
        client = Mock()
        client.send_message.return_value = {'MessageId': 'test-message-id-123'}
        client.receive_message.return_value = {'Messages': []}
        client.delete_message.return_value = {}
        client.get_queue_attributes.return_value = {
            'Attributes': {
                'ApproximateNumberOfMessages': '0',
                'ApproximateNumberOfMessagesNotVisible': '0',
                'QueueArn': 'arn:aws:sqs:ap-northeast-1:123456789012:test-queue'
            }
        }
        return client
    
    @pytest.fixture
    def queue_manager(self, mock_sqs_client):
        """建立佇列管理器"""
        manager = SQSQueueManager()
        manager.sqs_client = mock_sqs_client
        return manager
    
    @pytest.mark.asyncio
    async def test_send_message_success(self, queue_manager, mock_sqs_client):
        """測試發送訊息成功"""
        message_data = {
            'type': 'send_message',
            'batch_id': str(uuid4()),
            'content': 'Test message'
        }
        
        result = await queue_manager.send_message('send_queue', message_data)
        
        assert result == 'test-message-id-123'
        mock_sqs_client.send_message.assert_called_once()
        call_args = mock_sqs_client.send_message.call_args[1]
        assert 'QueueUrl' in call_args
        assert 'MessageBody' in call_args
        
        # 驗證訊息內容
        body = json.loads(call_args['MessageBody'])
        assert body['type'] == 'send_message'
        assert body['content'] == 'Test message'
    
    @pytest.mark.asyncio
    async def test_send_message_with_attributes(self, queue_manager, mock_sqs_client):
        """測試發送訊息包含屬性"""
        message_data = {'test': 'data'}
        
        await queue_manager.send_message(
            'send_queue', 
            message_data,
            message_group_id='test-group'
        )
        
        call_args = mock_sqs_client.send_message.call_args[1]
        assert 'MessageGroupId' in call_args
        assert call_args['MessageGroupId'] == 'test-group'
        assert 'MessageAttributes' in call_args
    
    @pytest.mark.asyncio
    async def test_receive_messages_success(self, queue_manager, mock_sqs_client):
        """測試接收訊息成功"""
        mock_messages = [{
            'MessageId': 'msg-123',
            'ReceiptHandle': 'receipt-123',
            'Body': json.dumps({'test': 'data'}),
            'Attributes': {},
            'MessageAttributes': {}
        }]
        mock_sqs_client.receive_message.return_value = {'Messages': mock_messages}
        
        messages = await queue_manager.receive_messages('send_queue')
        
        assert len(messages) == 1
        assert messages[0]['message_id'] == 'msg-123'
        assert messages[0]['body']['test'] == 'data'
        assert messages[0]['queue_name'] == 'send_queue'
    
    @pytest.mark.asyncio
    async def test_delete_message_success(self, queue_manager, mock_sqs_client):
        """測試刪除訊息成功"""
        result = await queue_manager.delete_message('send_queue', 'receipt-123')
        
        assert result is True
        mock_sqs_client.delete_message.assert_called_once_with(
            QueueUrl=queue_manager.queue_urls['send_queue'],
            ReceiptHandle='receipt-123'
        )
    
    @pytest.mark.asyncio
    async def test_get_queue_statistics(self, queue_manager, mock_sqs_client):
        """測試取得佇列統計"""
        stats = await queue_manager.get_queue_statistics()
        
        assert 'send_queue' in stats
        assert 'batch_queue' in stats
        assert stats['send_queue']['approximate_number_of_messages'] == 0


class TestSQSWorker:
    """測試 SQS Worker"""
    
    @pytest.fixture
    def mock_queue_manager(self):
        """模擬佇列管理器"""
        manager = AsyncMock()
        manager.get_queue_statistics.return_value = {
            'send_queue': {'approximate_number_of_messages': 0},
            'batch_queue': {'approximate_number_of_messages': 0}
        }
        manager.receive_messages.return_value = []
        manager.delete_message.return_value = True
        return manager
    
    @pytest.fixture
    def worker(self, mock_queue_manager):
        """建立 Worker"""
        worker = SQSWorker()
        # 縮短測試時間
        worker.poll_interval = 0.1
        worker.max_messages_per_poll = 1
        return worker
    
    @pytest.mark.asyncio
    async def test_worker_configuration_validation(self, worker):
        """測試 Worker 配置驗證"""
        with patch('app.services.sqs_queue_manager.sqs_queue_manager') as mock_manager:
            mock_manager.get_queue_statistics.return_value = {
                'send_queue': {'approximate_number_of_messages': 0},
                'batch_queue': {'approximate_number_of_messages': 0}
            }
            
            result = await worker._validate_configuration()
            assert result is True
    
    @pytest.mark.asyncio
    async def test_handle_send_message(self, worker):
        """測試處理單一訊息"""
        message_data = {
            'batch_id': str(uuid4()),
            'message_id': '123',
            'channel': 'line',
            'content': 'Test message',
            'recipient': {'id': 'user123'}
        }
        
        result = await worker._handle_send_message(message_data)
        
        assert 'success' in result
        assert 'message_id' in result
        assert result['message_id'] == '123'
    
    @pytest.mark.asyncio
    async def test_handle_batch_send(self, worker):
        """測試處理批次訊息"""
        message_data = {
            'batch_id': str(uuid4()),
            'channel': 'line',
            'content': 'Batch message',
            'recipients': [
                {'id': 'user1', 'message_id': '001'},
                {'id': 'user2', 'message_id': '002'}
            ]
        }
        
        result = await worker._handle_batch_send(message_data)
        
        assert result['success'] is True
        assert result['total_count'] == 2
        assert 'results' in result
        assert len(result['results']) == 2


class TestSendServiceSQSIntegration:
    """測試發送服務 SQS 整合"""
    
    @pytest.fixture
    def mock_sqs_manager(self):
        """模擬 SQS 管理器"""
        manager = AsyncMock()
        manager.send_message.return_value = 'task-id-123'
        return manager
    
    @pytest.fixture
    def mock_crud(self):
        """模擬 CRUD 操作"""
        mock_batch = Mock()
        mock_batch.batch_id = uuid4()
        mock_batch.batch_name = 'test_batch'
        mock_batch.total_count = 2
        mock_batch.created_at = '2024-07-29T10:00:00'
        
        mock_message = Mock()
        mock_message.id = 123
        mock_message.created_at = '2024-07-29T10:00:00'
        
        with patch('app.services.send_service.crud_batch_send_record') as mock_batch_crud, \
             patch('app.services.send_service.crud_message_send_record') as mock_msg_crud:
            
            mock_batch_crud.create.return_value = mock_batch
            mock_msg_crud.create_batch.return_value = [mock_message, mock_message]
            
            yield {
                'batch_crud': mock_batch_crud,
                'message_crud': mock_msg_crud,
                'batch_record': mock_batch,
                'message_records': [mock_message, mock_message]
            }
    
    @pytest.mark.asyncio
    async def test_send_message_small_batch(self, mock_sqs_manager, mock_crud):
        """測試小批次發送 (使用單一訊息佇列)"""
        with patch('app.services.send_service.sqs_queue_manager', mock_sqs_manager):
            service = SendService()
            
            result = await service.send_message(
                content="Test message",
                channel="line",
                recipients=[
                    {"id": "user1"},
                    {"id": "user2"}
                ]
            )
            
            assert result['success'] is True
            assert result['status'] == 'queued'
            assert result['total_count'] == 2
            assert 'task_ids' in result
            
            # 驗證推送到單一訊息佇列
            assert mock_sqs_manager.send_message.call_count == 2
            calls = mock_sqs_manager.send_message.call_args_list
            assert all(call[1]['queue_name'] == 'send_queue' for call in calls)
    
    @pytest.mark.asyncio
    async def test_send_message_large_batch(self, mock_sqs_manager, mock_crud):
        """測試大批次發送 (使用批次佇列)"""
        with patch('app.services.send_service.sqs_queue_manager', mock_sqs_manager):
            service = SendService()
            
            # 建立大批次 (>5 個收件人)
            recipients = [{"id": f"user{i}"} for i in range(10)]
            
            result = await service.send_message(
                content="Batch message",
                channel="line",
                recipients=recipients
            )
            
            assert result['success'] is True
            assert result['status'] == 'queued'
            
            # 驗證推送到批次佇列
            assert mock_sqs_manager.send_message.call_count == 1
            call_args = mock_sqs_manager.send_message.call_args[1]
            assert call_args['queue_name'] == 'batch_queue'
            
            # 驗證批次資料
            message_data = call_args['message_data']
            assert message_data['type'] == 'batch_send'
            assert len(message_data['recipients']) == 10
    
    @pytest.mark.asyncio
    async def test_send_message_enqueue_failure(self, mock_crud):
        """測試佇列推送失敗處理"""
        mock_sqs_manager = AsyncMock()
        mock_sqs_manager.send_message.return_value = None  # 推送失敗
        
        with patch('app.services.send_service.sqs_queue_manager', mock_sqs_manager):
            service = SendService()
            
            result = await service.send_message(
                content="Test message",
                channel="line",
                recipients=[{"id": "user1"}]
            )
            
            assert result['success'] is False
            assert '佇列推送失敗' in result['error']
            assert result['status'] == 'failed'


class TestSQSSystemIntegration:
    """測試 SQS 系統整合"""
    
    @pytest.mark.asyncio
    async def test_end_to_end_message_flow(self):
        """測試端到端訊息流程"""
        # 這個測試需要實際的 LocalStack 或 AWS 環境
        # 目前作為整合測試的範例
        pass
    
    @pytest.mark.asyncio 
    async def test_error_handling_and_dlq(self):
        """測試錯誤處理和 DLQ 機制"""
        # 測試訊息處理失敗後進入 DLQ
        pass
    
    @pytest.mark.asyncio
    async def test_worker_graceful_shutdown(self):
        """測試 Worker 優雅關閉"""
        worker = SQSWorker()
        worker.poll_interval = 0.01  # 加快測試
        
        # 模擬佇列管理器
        with patch('app.services.sqs_queue_manager.sqs_queue_manager') as mock_manager:
            mock_manager.get_queue_statistics.return_value = {
                'send_queue': {'approximate_number_of_messages': 0},
                'batch_queue': {'approximate_number_of_messages': 0}
            }
            mock_manager.receive_messages.return_value = []
            
            # 啟動 Worker
            start_task = asyncio.create_task(worker.start())
            
            # 短暫等待後停止
            await asyncio.sleep(0.05)
            await worker.stop()
            
            # 確認 Worker 已停止
            try:
                await asyncio.wait_for(start_task, timeout=1.0)
            except asyncio.TimeoutError:
                pytest.fail("Worker did not stop gracefully")


if __name__ == "__main__":
    pytest.main([__file__])
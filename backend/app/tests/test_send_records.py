"""
發送記錄 Models 和 Repository 測試
"""

import pytest
from uuid import uuid4, UUID
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.batch_send_record import BatchSendRecord
from app.models.message_send_record import MessageSendRecord
from app.crud.batch_send_record import crud_batch_send_record
from app.crud.message_send_record import crud_message_send_record


class TestBatchSendRecord:
    """BatchSendRecord Model 測試"""
    
    def test_create_batch_record(self):
        """測試建立批次記錄"""
        batch = BatchSendRecord(
            batch_name="test_batch",
            total_count=10,
            success_count=5,
            failed_count=2,
            pending_count=3
        )
        
        assert batch.batch_name == "test_batch"
        assert batch.total_count == 10
        assert batch.success_count == 5
        assert batch.failed_count == 2
        assert batch.pending_count == 3
        assert batch.status == "pending"
        assert batch.version == 0
        assert isinstance(batch.batch_id, UUID)
    
    def test_to_dict(self):
        """測試轉換為字典"""
        batch = BatchSendRecord(
            batch_name="test_batch",
            total_count=10
        )
        
        result = batch.to_dict()
        
        assert result['batch_name'] == "test_batch"
        assert result['total_count'] == 10
        assert result['status'] == "pending"
        assert result['version'] == 0
        assert 'batch_id' in result
    
    def test_get_success_rate(self):
        """測試成功率計算"""
        batch = BatchSendRecord(
            total_count=10,
            success_count=8
        )
        
        assert batch.get_success_rate() == 80.0
        
        # 測試零除法
        batch_zero = BatchSendRecord(total_count=0)
        assert batch_zero.get_success_rate() == 0.0
    
    def test_is_completed(self):
        """測試完成狀態檢查"""
        batch_pending = BatchSendRecord(status="pending")
        batch_completed = BatchSendRecord(status="completed")
        batch_failed = BatchSendRecord(status="failed")
        
        assert not batch_pending.is_completed()
        assert batch_completed.is_completed()
        assert batch_failed.is_completed()
    
    def test_calculate_remaining_count(self):
        """測試剩餘數量計算"""
        batch = BatchSendRecord(
            total_count=10,
            success_count=6,
            failed_count=2
        )
        
        assert batch.calculate_remaining_count() == 2


class TestMessageSendRecord:
    """MessageSendRecord Model 測試"""
    
    def test_create_message_record(self):
        """測試建立發送記錄"""
        batch_id = uuid4()
        message = MessageSendRecord(
            batch_id=batch_id,
            channel="line",
            content="測試訊息",
            recipient_id="user123",
            recipient_type="line"
        )
        
        assert message.batch_id == batch_id
        assert message.channel == "line"
        assert message.content == "測試訊息"
        assert message.recipient_id == "user123"
        assert message.recipient_type == "line"
        assert message.status == "pending"
    
    def test_to_dict(self):
        """測試轉換為字典"""
        batch_id = uuid4()
        message = MessageSendRecord(
            batch_id=batch_id,
            channel="line",
            content="測試訊息",
            recipient_id="user123",
            recipient_type="line"
        )
        
        result = message.to_dict()
        
        assert result['batch_id'] == str(batch_id)
        assert result['channel'] == "line"
        assert result['content'] == "測試訊息"
        assert result['status'] == "pending"
    
    def test_status_checks(self):
        """測試狀態檢查方法"""
        message = MessageSendRecord()
        
        # 預設狀態為 pending
        assert message.is_pending()
        assert not message.is_success()
        assert not message.is_failed()
        
        # 測試 success 狀態
        message.status = "success"
        assert not message.is_pending()
        assert message.is_success()
        assert not message.is_failed()
        
        # 測試 failed 狀態
        message.status = "failed"
        assert not message.is_pending()
        assert not message.is_success()
        assert message.is_failed()
    
    def test_mark_methods(self):
        """測試狀態標記方法"""
        message = MessageSendRecord()
        
        # 測試標記為發送中
        message.mark_as_sending()
        assert message.status == "sending"
        
        # 測試標記為成功
        message.mark_as_success()
        assert message.status == "success"
        assert message.error_message is None
        
        # 測試標記為失敗
        message.mark_as_failed("發送失敗")
        assert message.status == "failed"
        assert message.error_message == "發送失敗"


# 由於我們需要資料庫連接來測試 Repository，這裡提供測試結構
# 實際測試需要在有資料庫環境的情況下執行

class TestBatchSendRecordCRUD:
    """BatchSendRecord CRUD 測試"""
    
    def test_create_batch_send_record(self):
        """測試建立批次記錄"""
        # batch_data = {
        #     "batch_name": "test_batch",
        #     "total_count": 5
        # }
        # 
        # batch = crud_batch_send_record.create(batch_data=batch_data)
        # assert batch.batch_name == "test_batch"
        # assert batch.total_count == 5
        pass


class TestMessageSendRecordCRUD:
    """MessageSendRecord CRUD 測試"""
    
    def test_create_message_send_record(self):
        """測試建立發送記錄"""
        # message_data = {
        #     "batch_id": "some-uuid",
        #     "channel": "line",
        #     "content": "test message"
        # }
        # 
        # message = crud_message_send_record.create(message_data=message_data)
        # assert message.channel == "line"
        pass
    
    def test_create_message_send_records_batch(self):
        """測試批量建立發送記錄"""
        # messages_data = [
        #     {"batch_id": "uuid", "channel": "line", "content": "msg1"},
        #     {"batch_id": "uuid", "channel": "line", "content": "msg2"}
        # ]
        # 
        # messages = crud_message_send_record.create_batch(messages_data=messages_data)
        # assert len(messages) == 2
        pass


if __name__ == "__main__":
    pytest.main([__file__])
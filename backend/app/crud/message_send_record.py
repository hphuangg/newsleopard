"""
MessageSendRecord CRUD 操作

個別發送記錄的 CRUD 實作。

TODO: 未來需要統一 DB Session 管理，類似 JPA EntityManager 的概念
      目前每個 CRUD 類別都自己管理 Session，應該改為依賴注入模式
      參考: app.db.database.get_db() 函數
"""

from typing import List, Dict, Any
from contextlib import contextmanager
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.models.message_send_record import MessageSendRecord
from app.db.database import SessionLocal


class MessageSendRecordCRUD:
    """個別發送記錄的 CRUD 操作類別 - 管理自己的 DB Session"""
    
    @contextmanager
    def _get_db(self):
        """獲取資料庫 session (Context Manager)"""
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()
    
    def create(self, *, message_data: Dict[str, Any]) -> MessageSendRecord:
        """建立發送記錄"""
        with self._get_db() as db:
            try:
                message = MessageSendRecord(**message_data)
                db.add(message)
                db.commit()
                db.refresh(message)
                return message
            except IntegrityError as e:
                db.rollback()
                raise ValueError(f"發送記錄建立失敗: {str(e)}")
            except SQLAlchemyError as e:
                db.rollback()
                raise RuntimeError(f"資料庫操作失敗: {str(e)}")
    
    def create_batch(self, *, messages_data: List[Dict[str, Any]]) -> List[MessageSendRecord]:
        """批量建立發送記錄"""
        with self._get_db() as db:
            try:
                messages = [MessageSendRecord(**data) for data in messages_data]
                db.add_all(messages)
                db.commit()
                for message in messages:
                    db.refresh(message)
                return messages
            except IntegrityError as e:
                db.rollback()
                raise ValueError(f"批量建立失敗: {str(e)}")
            except SQLAlchemyError as e:
                db.rollback()
                raise RuntimeError(f"資料庫操作失敗: {str(e)}")


# 建立全域實例
crud_message_send_record = MessageSendRecordCRUD()
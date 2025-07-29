"""
BatchSendRecord CRUD 操作

批次發送記錄的 CRUD 實作。

TODO: 未來需要統一 DB Session 管理，類似 JPA EntityManager 的概念
      目前每個 CRUD 類別都自己管理 Session，應該改為依賴注入模式
      參考: app.db.database.get_db() 函數
"""

from typing import Dict, Any
from contextlib import contextmanager
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.models.batch_send_record import BatchSendRecord
from app.db.database import SessionLocal


class BatchSendRecordCRUD:
    """批次發送記錄的 CRUD 操作類別 - 管理自己的 DB Session"""
    
    @contextmanager
    def _get_db(self):
        """獲取資料庫 session (Context Manager)"""
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()
    
    def create(self, *, batch_data: Dict[str, Any]) -> BatchSendRecord:
        """建立批次記錄"""
        with self._get_db() as db:
            try:
                batch = BatchSendRecord(**batch_data)
                db.add(batch)
                db.commit()
                db.refresh(batch)
                return batch
            except IntegrityError as e:
                db.rollback()
                raise ValueError(f"批次記錄建立失敗: {str(e)}")
            except SQLAlchemyError as e:
                db.rollback()
                raise RuntimeError(f"資料庫操作失敗: {str(e)}")


# 建立全域實例
crud_batch_send_record = BatchSendRecordCRUD()
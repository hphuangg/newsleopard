"""
MessageSendRecord Model

個別發送記錄的 SQLAlchemy 模型定義。
從 backend/app/models/message_send_record.py 遷移而來。
"""

from typing import Dict

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.orm import relationship

from shared.db.database import Base


class MessageSendRecord(Base):
    """發送記錄表"""
    
    __tablename__ = "message_send_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    batch_id = Column(PostgreSQLUUID(as_uuid=True), ForeignKey("batch_send_records.batch_id"), nullable=False)
    channel = Column(String(20), nullable=False)  # line, sms, email
    content = Column(Text, nullable=False)
    recipient_id = Column(String(255), nullable=False)
    recipient_type = Column(String(50), nullable=False)
    status = Column(String(20), nullable=False, default="pending")  # pending, sending, success, failed
    error_message = Column(Text, nullable=True)
    sent_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, default=func.now(), onupdate=func.now())

    # 關聯
    batch = relationship("BatchSendRecord", back_populates="messages")

    def __repr__(self) -> str:
        return f"<MessageSendRecord(id={self.id}, batch_id={self.batch_id}, status={self.status})>"
    
    def to_dict(self) -> Dict:
        """轉換為字典格式"""
        return {
            'id': self.id,
            'batch_id': str(self.batch_id),
            'channel': self.channel,
            'content': self.content,
            'recipient_id': self.recipient_id,
            'recipient_type': self.recipient_type,
            'status': self.status,
            'error_message': self.error_message,
            'sent_at': self.sent_at.isoformat() if self.sent_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
    
    def is_pending(self) -> bool:
        """檢查是否為待處理狀態"""
        return self.status == "pending"
    
    def is_success(self) -> bool:
        """檢查是否發送成功"""
        return self.status == "success"
    
    def is_failed(self) -> bool:
        """檢查是否發送失敗"""
        return self.status == "failed"
    
    def mark_as_sending(self) -> None:
        """標記為發送中"""
        self.status = "sending"
        self.updated_at = func.now()
    
    def mark_as_success(self) -> None:
        """標記為發送成功"""
        self.status = "success"
        self.sent_at = func.now()
        self.updated_at = func.now()
        self.error_message = None
    
    def mark_as_failed(self, error_message: str) -> None:
        """標記為發送失敗"""
        self.status = "failed"
        self.error_message = error_message
        self.updated_at = func.now()
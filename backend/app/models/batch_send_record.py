"""
BatchSendRecord Model

批次發送記錄的 SQLAlchemy 模型定義。
"""

from typing import Dict
from uuid import uuid4

from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.orm import relationship

from app.db.database import Base


class BatchSendRecord(Base):
    """批次發送記錄表"""
    
    __tablename__ = "batch_send_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    batch_id = Column(PostgreSQLUUID(as_uuid=True), unique=True, nullable=False, default=uuid4)
    batch_name = Column(String(255), nullable=True)
    total_count = Column(Integer, nullable=False)
    success_count = Column(Integer, default=0, nullable=False)
    failed_count = Column(Integer, default=0, nullable=False)
    pending_count = Column(Integer, default=0, nullable=False)
    status = Column(String(20), nullable=False, default="pending")
    version = Column(Integer, default=0, nullable=False)  # 樂觀鎖版本號
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, default=func.now(), onupdate=func.now())

    # 關聯
    messages = relationship("MessageSendRecord", back_populates="batch", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<BatchSendRecord(batch_id={self.batch_id}, status={self.status})>"
    
    def to_dict(self) -> Dict:
        """轉換為字典格式"""
        return {
            'id': self.id,
            'batch_id': str(self.batch_id),
            'batch_name': self.batch_name,
            'total_count': self.total_count,
            'success_count': self.success_count,
            'failed_count': self.failed_count,
            'pending_count': self.pending_count,
            'status': self.status,
            'version': self.version,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
    
    def get_success_rate(self) -> float:
        """計算成功率"""
        if self.total_count == 0:
            return 0.0
        return (self.success_count / self.total_count) * 100
    
    def is_completed(self) -> bool:
        """檢查批次是否已完成"""
        return self.status in ['completed', 'failed']
    
    def calculate_remaining_count(self) -> int:
        """計算剩餘待處理數量"""
        return self.total_count - self.success_count - self.failed_count



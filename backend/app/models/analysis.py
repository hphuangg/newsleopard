from sqlalchemy import Column, Integer, String, Text, DECIMAL, DateTime
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from uuid import uuid4

from app.db.database import Base


class AnalysisRecord(Base):
    """分析記錄表 - 儲存每次文案分析的完整記錄"""
    
    __tablename__ = "analysis_records"

    # 主鍵和識別碼
    id = Column(Integer, primary_key=True, autoincrement=True, comment="內部連續ID")
    analysis_id = Column(UUID(as_uuid=True), unique=True, nullable=False, 
                        default=uuid4, comment="對外分析記錄識別碼")
    
    # 輸入資料
    content = Column(Text, nullable=False, comment="Line文案內容")
    target_audience = Column(String(50), nullable=False, comment="目標受眾")
    send_scenario = Column(String(50), nullable=False, comment="發送場景")
    
    # 分析結果
    attractiveness = Column(DECIMAL(3, 1), nullable=True, comment="吸引力評分 (1.0-10.0)")
    readability = Column(DECIMAL(3, 1), nullable=True, comment="可讀性評分 (1.0-10.0)")
    line_compatibility = Column(DECIMAL(3, 1), nullable=True, comment="Line平台相容性評分 (1.0-10.0)")
    overall_score = Column(DECIMAL(3, 1), nullable=True, comment="整體評分 (1.0-10.0)")
    sentiment = Column(String(100), nullable=True, comment="情感傾向分析")
    suggestions = Column(JSONB, nullable=True, comment="改善建議列表")
    
    # AI 處理資訊
    ai_model_used = Column(String(100), nullable=True, comment="使用的AI模型名稱")
    processing_time = Column(DECIMAL(6, 3), nullable=True, comment="處理時間(秒)")
    
    # 狀態管理
    status = Column(String(20), nullable=False, default="pending", comment="處理狀態")
    error_message = Column(Text, nullable=True, comment="錯誤訊息")
    
    # 時間戳記
    created_at = Column(DateTime(timezone=True), nullable=False, 
                       default=func.now(), comment="建立時間")
    updated_at = Column(DateTime(timezone=True), nullable=False, 
                       default=func.now(), onupdate=func.now(), comment="更新時間")

    def __repr__(self):
        return f"<AnalysisRecord(analysis_id={self.analysis_id}, status={self.status})>"
    
    def to_dict(self):
        """轉換為字典格式"""
        return {
            'id': self.id,
            'analysis_id': str(self.analysis_id),
            'content': self.content,
            'target_audience': self.target_audience,
            'send_scenario': self.send_scenario,
            'attractiveness': float(self.attractiveness) if self.attractiveness else None,
            'readability': float(self.readability) if self.readability else None,
            'line_compatibility': float(self.line_compatibility) if self.line_compatibility else None,
            'overall_score': float(self.overall_score) if self.overall_score else None,
            'sentiment': self.sentiment,
            'suggestions': self.suggestions,
            'ai_model_used': self.ai_model_used,
            'processing_time': float(self.processing_time) if self.processing_time else None,
            'status': self.status,
            'error_message': self.error_message,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
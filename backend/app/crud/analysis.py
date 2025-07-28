from typing import Optional
from uuid import UUID
from contextlib import contextmanager
from sqlalchemy.orm import Session
from app.models.analysis import AnalysisRecord
from app.schemas.analysis import AnalysisCreate
from app.db.database import SessionLocal


class AnalysisCRUD:
    """分析記錄的 CRUD 操作類別 - 管理自己的 DB Session"""
    
    @contextmanager
    def _get_db(self):
        """獲取資料庫 session (Context Manager)"""
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()
    
    def create(self, *, obj_in: AnalysisCreate) -> AnalysisRecord:
        """建立新的分析記錄"""
        with self._get_db() as db:
            db_obj = AnalysisRecord(
                content=obj_in.content,
                target_audience=obj_in.target_audience.value,
                send_scenario=obj_in.send_scenario.value,
                status="pending"
            )
            db.add(db_obj)
            db.commit()
            db.refresh(db_obj)
            return db_obj
    
    def get_by_analysis_id(self, *, analysis_id: UUID) -> Optional[AnalysisRecord]:
        """根據 analysis_id 查詢分析記錄"""
        with self._get_db() as db:
            return db.query(AnalysisRecord).filter(AnalysisRecord.analysis_id == analysis_id).first()
    
    def update(self, *, analysis_id: UUID, **update_data) -> Optional[AnalysisRecord]:
        """更新分析記錄"""
        with self._get_db() as db:
            db_obj = db.query(AnalysisRecord).filter(AnalysisRecord.analysis_id == analysis_id).first()
            if not db_obj:
                return None
            
            for field, value in update_data.items():
                if hasattr(db_obj, field):
                    setattr(db_obj, field, value)
            
            db.commit()
            db.refresh(db_obj)
            return db_obj


# 建立全域實例
crud_analysis = AnalysisCRUD()
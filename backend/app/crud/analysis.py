from typing import Optional
from uuid import UUID
from sqlalchemy.orm import Session
from app.models.analysis import AnalysisRecord
from app.schemas.analysis import AnalysisCreate


class AnalysisCRUD:
    """分析記錄的 CRUD 操作類別"""
    
    def create(self, db: Session, *, obj_in: AnalysisCreate) -> AnalysisRecord:
        """建立新的分析記錄"""
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
    
    def get_by_analysis_id(self, db: Session, *, analysis_id: UUID) -> Optional[AnalysisRecord]:
        """根據 analysis_id 查詢分析記錄"""
        return db.query(AnalysisRecord).filter(AnalysisRecord.analysis_id == analysis_id).first()


# 建立全域實例
crud_analysis = AnalysisCRUD()

# 保持向後相容性
def create_analysis_record(db: Session, analysis_data: AnalysisCreate) -> AnalysisRecord:
    """建立新的分析記錄 (舊版本相容性函數)"""
    return crud_analysis.create(db, obj_in=analysis_data)
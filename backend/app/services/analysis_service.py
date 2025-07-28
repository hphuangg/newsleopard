"""分析服務 - 處理文案分析的業務邏輯"""

import time
from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session
from uuid import UUID

from app.schemas.analysis import AnalysisCreate, AnalysisResponse
from app.models.analysis import AnalysisRecord
from app.crud.analysis import crud_analysis
from app.services.ai_client import OpenAIClient, AIAnalysisError


class AnalysisService:
    """分析服務類別"""
    
    def __init__(self, ai_client: Optional[OpenAIClient] = None):
        self.ai_client = ai_client or OpenAIClient()
    
    async def create_and_analyze(
        self, 
        db: Session, 
        analysis_data: AnalysisCreate
    ) -> AnalysisRecord:
        """建立分析記錄並執行 AI 分析"""
        
        # 1. 建立 pending 狀態的分析記錄
        db_analysis = crud_analysis.create(db, obj_in=analysis_data)
        
        start_time = time.time()
        
        try:
            # 2. 標記為處理中
            db_analysis.status = "processing"
            db.commit()
            
            # 3. 調用 AI API 進行分析
            ai_result = await self.ai_client.analyze_content(
                content=analysis_data.content,
                target_audience=analysis_data.target_audience.value,
                send_scenario=analysis_data.send_scenario.value
            )
            
            # 4. 計算處理時間
            processing_time = time.time() - start_time
            
            # 5. 更新分析結果
            db_analysis = self._update_analysis_results(
                db=db,
                db_analysis=db_analysis,
                ai_result=ai_result,
                processing_time=processing_time
            )
            
            return db_analysis
            
        except AIAnalysisError as e:
            # AI 分析失敗，標記為失敗狀態
            processing_time = time.time() - start_time
            return self._mark_analysis_failed(
                db=db,
                db_analysis=db_analysis,
                error_message=str(e),
                processing_time=processing_time
            )
        
        except Exception as e:
            # 其他未預期的錯誤
            processing_time = time.time() - start_time
            return self._mark_analysis_failed(
                db=db,
                db_analysis=db_analysis,
                error_message=f"系統錯誤: {str(e)}",
                processing_time=processing_time
            )
    
    def get_analysis_by_id(
        self, 
        db: Session, 
        analysis_id: UUID
    ) -> Optional[AnalysisRecord]:
        """根據 analysis_id 查詢分析記錄"""
        return crud_analysis.get_by_analysis_id(db, analysis_id=analysis_id)
    
    def _update_analysis_results(
        self,
        db: Session,
        db_analysis: AnalysisRecord,
        ai_result: dict,
        processing_time: float
    ) -> AnalysisRecord:
        """更新分析結果到資料庫"""
        
        db_analysis.attractiveness = ai_result["attractiveness"]
        db_analysis.readability = ai_result["readability"] 
        db_analysis.line_compatibility = ai_result["line_compatibility"]
        db_analysis.overall_score = ai_result["overall_score"]
        db_analysis.sentiment = ai_result["sentiment"]
        db_analysis.suggestions = ai_result["suggestions"]
        db_analysis.ai_model_used = self.ai_client.model
        db_analysis.processing_time = processing_time
        db_analysis.status = "completed"
        db_analysis.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(db_analysis)
        
        return db_analysis
    
    def _mark_analysis_failed(
        self,
        db: Session,
        db_analysis: AnalysisRecord,
        error_message: str,
        processing_time: float
    ) -> AnalysisRecord:
        """標記分析失敗"""
        
        db_analysis.status = "failed"
        db_analysis.error_message = error_message
        db_analysis.processing_time = processing_time
        db_analysis.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(db_analysis)
        
        return db_analysis
    
    def convert_to_response(self, db_analysis: AnalysisRecord) -> AnalysisResponse:
        """轉換為 API 回應格式"""
        from app.schemas.analysis import AnalysisResults
        
        # 如果分析完成，包含結果
        results = None
        if db_analysis.status == "completed":
            results = AnalysisResults(
                attractiveness=db_analysis.attractiveness,
                readability=db_analysis.readability,
                line_compatibility=db_analysis.line_compatibility,
                overall_score=db_analysis.overall_score,
                sentiment=db_analysis.sentiment,
                suggestions=db_analysis.suggestions
            )
        
        return AnalysisResponse(
            analysis_id=db_analysis.analysis_id,
            status=db_analysis.status,
            created_at=db_analysis.created_at,
            results=results
        )


# 建立全域實例
def get_analysis_service() -> AnalysisService:
    """獲取分析服務實例"""
    return AnalysisService()
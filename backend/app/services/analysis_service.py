"""分析服務 - 處理文案分析的業務邏輯"""

import time
from datetime import datetime
from typing import Optional
from uuid import UUID

from app.schemas.analysis import AnalysisCreate, AnalysisResponse
from app.models.analysis import AnalysisRecord
from app.crud.analysis import AnalysisCRUD
from app.services.ai_client import AIClientBase, get_default_ai_client
from app.core.exceptions import AIServiceException


class AnalysisService:
    """分析服務類別 - 純業務邏輯，不直接操作資料庫」"""
    
    def __init__(
        self, 
        ai_client: Optional[AIClientBase] = None,
        crud: Optional[AnalysisCRUD] = None
    ):
        self.ai_client = ai_client or get_default_ai_client()
        self.crud = crud or AnalysisCRUD()
    
    async def create_and_analyze(
        self, 
        analysis_data: AnalysisCreate
    ) -> AnalysisRecord:
        """建立分析記錄並執行 AI 分析"""
        
        # 1. 建立 pending 狀態的分析記錄
        db_analysis = self.crud.create(obj_in=analysis_data)
        
        start_time = time.time()
        
        try:
            # 2. 標記為處理中
            self.crud.update(
                analysis_id=db_analysis.analysis_id,
                status="processing"
            )
            
            # 3. 調用 AI API 進行分析
            ai_result = await self.ai_client.analyze_content(
                content=analysis_data.content,
                target_audience=analysis_data.target_audience.value,
                send_scenario=analysis_data.send_scenario.value
            )
            
            # 4. 計算處理時間
            processing_time = time.time() - start_time
            
            # 5. 更新分析結果
            updated_analysis = self.crud.update(
                analysis_id=db_analysis.analysis_id,
                attractiveness=ai_result["attractiveness"],
                readability=ai_result["readability"],
                line_compatibility=ai_result["line_compatibility"],
                overall_score=ai_result["overall_score"],
                sentiment=ai_result["sentiment"],
                suggestions=ai_result["suggestions"],
                ai_model_used=self.ai_client.model,
                processing_time=processing_time,
                status="completed",
                updated_at=datetime.utcnow()
            )
            
            return updated_analysis or db_analysis
            
        except AIServiceException as e:
            # AI 分析失敗，標記為失敗狀態
            processing_time = time.time() - start_time
            failed_analysis = self.crud.update(
                analysis_id=db_analysis.analysis_id,
                status="failed",
                error_message=e.message,
                processing_time=processing_time,
                updated_at=datetime.utcnow()
            )
            return failed_analysis or db_analysis
        
        except Exception as e:
            # 其他未預期的錯誤
            processing_time = time.time() - start_time
            failed_analysis = self.crud.update(
                analysis_id=db_analysis.analysis_id,
                status="failed",
                error_message=f"系統錯誤: {str(e)}",
                processing_time=processing_time,
                updated_at=datetime.utcnow()
            )
            return failed_analysis or db_analysis
    
    def get_analysis_by_id(
        self, 
        analysis_id: UUID
    ) -> Optional[AnalysisRecord]:
        """根據 analysis_id 查詢分析記錄"""
        return self.crud.get_by_analysis_id(analysis_id=analysis_id)
    
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
"""分析 API 端點"""

from uuid import UUID
from fastapi import APIRouter, HTTPException, Depends, status
from app.services.analysis_service import AnalysisService
from app.schemas.analysis import AnalysisCreate, AnalysisResponse
from app.core.dependencies import get_analysis_service
from app.core.error_handlers import handle_service_exceptions


router = APIRouter()


@router.post("/analyze", response_model=AnalysisResponse, status_code=status.HTTP_201_CREATED)
# @handle_service_exceptions  # 暫時註解掉來看詳細錯誤
async def create_analysis(
    analysis_data: AnalysisCreate,
    analysis_service: AnalysisService = Depends(get_analysis_service)
) -> AnalysisResponse:
    """
    建立新的文案分析
    
    - **content**: Line文案內容 (1-2000字)
    - **target_audience**: 目標受眾 (B2B, B2C, 電商)
    - **send_scenario**: 發送場景 (official_account_push, group_message, one_on_one_service)
    
    回傳分析記錄，包含 analysis_id 用於後續查詢結果
    """
    # 使用分析服務建立並執行分析
    db_analysis = await analysis_service.create_and_analyze(analysis_data)
    
    # 轉換為 API 回應格式
    return analysis_service.convert_to_response(db_analysis)


@router.get("/analyze/{analysis_id}", response_model=AnalysisResponse)
@handle_service_exceptions
async def get_analysis(
    analysis_id: UUID,
    analysis_service: AnalysisService = Depends(get_analysis_service)
) -> AnalysisResponse:
    """
    查詢分析結果
    
    - **analysis_id**: 分析記錄的 UUID 識別碼
    
    回傳分析記錄和結果（如果已完成）
    """
    # 查詢分析記錄
    db_analysis = analysis_service.get_analysis_by_id(analysis_id)
    
    if not db_analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "ANALYSIS_NOT_FOUND",
                    "message": f"找不到分析記錄: {analysis_id}"
                }
            }
        )
    
    # 轉換為 API 回應格式
    return analysis_service.convert_to_response(db_analysis)
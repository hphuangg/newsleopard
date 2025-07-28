"""分析 API 端點"""

from uuid import UUID
from fastapi import APIRouter, HTTPException, Depends, status
from app.services.analysis_service import AnalysisService, get_analysis_service
from app.schemas.analysis import AnalysisCreate, AnalysisResponse
from app.core.exceptions import AIServiceException, BusinessLogicException, SystemException


router = APIRouter()


@router.post("/analyze", response_model=AnalysisResponse, status_code=status.HTTP_201_CREATED)
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
    try:
        # 使用分析服務建立並執行分析
        db_analysis = await analysis_service.create_and_analyze(analysis_data)
        
        # 轉換為 API 回應格式
        return analysis_service.convert_to_response(db_analysis)
        
    except AIServiceException as e:
        # AI 服務錯誤 - 根據錯誤類型回傳適當的 HTTP 狀態碼
        if "rate_limit" in e.code.lower():
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=e.to_dict(),
                headers={"Retry-After": str(e.retry_after)} if e.retry_after else None
            )
        elif "quota" in e.code.lower():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=e.to_dict()
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=e.to_dict()
            )
    
    except BusinessLogicException as e:
        # 業務邏輯錯誤 - 400 Bad Request
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.to_dict()
        )
    
    except SystemException as e:
        # 系統錯誤 - 500 Internal Server Error
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=e.to_dict()
        )
    
    except Exception as e:
        # 未預期的錯誤
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "系統發生未預期的錯誤"
                }
            }
        )


@router.get("/analyze/{analysis_id}", response_model=AnalysisResponse)
async def get_analysis(
    analysis_id: UUID,
    analysis_service: AnalysisService = Depends(get_analysis_service)
) -> AnalysisResponse:
    """
    查詢分析結果
    
    - **analysis_id**: 分析記錄的 UUID 識別碼
    
    回傳分析記錄和結果（如果已完成）
    """
    try:
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
        
    except HTTPException:
        # 重新拋出已處理的 HTTP 異常
        raise
    
    except Exception as e:
        # 未預期的錯誤
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "系統發生未預期的錯誤"
                }
            }
        )
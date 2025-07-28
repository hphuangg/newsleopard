"""統一的錯誤處理工具"""

from fastapi import HTTPException, status
from app.core.exceptions import AIServiceException, BusinessLogicException, SystemException


def handle_service_exceptions(func):
    """Service 異常處理裝飾器"""
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except AIServiceException as e:
            raise convert_ai_exception_to_http(e)
        except BusinessLogicException as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=e.to_dict()
            )
        except SystemException as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=e.to_dict()
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "error": {
                        "code": "INTERNAL_ERROR",
                        "message": "系統發生未預期的錯誤"
                    }
                }
            )
    return wrapper


def convert_ai_exception_to_http(e: AIServiceException) -> HTTPException:
    """將 AI 服務異常轉換為 HTTP 異常"""
    error_code = e.code.lower()
    
    if "rate_limit" in error_code:
        headers = {"Retry-After": str(e.retry_after)} if e.retry_after else None
        return HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=e.to_dict(),
            headers=headers
        )
    elif "quota" in error_code:
        return HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=e.to_dict()
        )
    else:
        return HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=e.to_dict()
        )
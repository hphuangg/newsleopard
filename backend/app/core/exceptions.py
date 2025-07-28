"""統一的異常和錯誤處理"""

from enum import Enum
from typing import Optional, Dict, Any


class AnalysisErrorCode(str, Enum):
    """分析錯誤代碼"""
    # AI 服務相關錯誤
    AI_SERVICE_UNAVAILABLE = "AI_SERVICE_UNAVAILABLE"
    AI_RATE_LIMIT_EXCEEDED = "AI_RATE_LIMIT_EXCEEDED" 
    AI_QUOTA_EXCEEDED = "AI_QUOTA_EXCEEDED"
    AI_INVALID_RESPONSE = "AI_INVALID_RESPONSE"
    AI_NETWORK_ERROR = "AI_NETWORK_ERROR"
    AI_AUTHENTICATION_ERROR = "AI_AUTHENTICATION_ERROR"
    
    # 業務邏輯錯誤
    INVALID_CONTENT = "INVALID_CONTENT"
    INVALID_TARGET_AUDIENCE = "INVALID_TARGET_AUDIENCE"
    INVALID_SEND_SCENARIO = "INVALID_SEND_SCENARIO"
    
    # 系統錯誤
    DATABASE_ERROR = "DATABASE_ERROR"
    INTERNAL_ERROR = "INTERNAL_ERROR"
    CONFIGURATION_ERROR = "CONFIGURATION_ERROR"


class AnalysisException(Exception):
    """分析相關的基礎異常類別"""
    
    def __init__(
        self, 
        code: AnalysisErrorCode, 
        message: str,
        details: Optional[Dict[str, Any]] = None,
        retry_after: Optional[int] = None
    ):
        self.code = code
        self.message = message
        self.details = details or {}
        self.retry_after = retry_after  # 建議重試間隔(秒)
        super().__init__(message)
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式，用於 API 回應"""
        result = {
            "error": {
                "code": self.code.value,
                "message": self.message
            }
        }
        
        if self.details:
            result["error"]["details"] = self.details
            
        if self.retry_after:
            result["retry_after"] = self.retry_after
            
        return result


class AIServiceException(AnalysisException):
    """AI 服務相關異常"""
    pass


class BusinessLogicException(AnalysisException):
    """業務邏輯異常"""
    pass


class SystemException(AnalysisException):
    """系統異常"""
    pass


# 便利函數用於建立常見異常
def create_ai_rate_limit_error(retry_after: int = 60) -> AIServiceException:
    """建立 AI 服務限流錯誤"""
    return AIServiceException(
        code=AnalysisErrorCode.AI_RATE_LIMIT_EXCEEDED,
        message="AI 服務使用量超限，請稍後重試",
        retry_after=retry_after
    )


def create_ai_quota_exceeded_error() -> AIServiceException:
    """建立 AI 服務配額超限錯誤"""
    return AIServiceException(
        code=AnalysisErrorCode.AI_QUOTA_EXCEEDED,
        message="AI 服務配額不足，請聯繫管理員"
    )


def create_ai_invalid_response_error(details: str) -> AIServiceException:
    """建立 AI 回應格式錯誤"""
    return AIServiceException(
        code=AnalysisErrorCode.AI_INVALID_RESPONSE,
        message="AI 回應格式錯誤",
        details={"error_details": details}
    )


def create_configuration_error(setting_name: str) -> SystemException:
    """建立配置錯誤"""
    return SystemException(
        code=AnalysisErrorCode.CONFIGURATION_ERROR,
        message=f"配置錯誤: {setting_name} 未設定或無效"
    )
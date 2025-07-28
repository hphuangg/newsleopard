from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime
from uuid import UUID
from enum import Enum


class TargetAudienceEnum(str, Enum):
    """目標受眾枚舉"""
    B2B = "B2B"
    B2C = "B2C"
    ECOMMERCE = "電商"


class SendScenarioEnum(str, Enum):
    """發送場景枚舉"""
    OFFICIAL_ACCOUNT_PUSH = "official_account_push"
    GROUP_MESSAGE = "group_message"
    ONE_ON_ONE_SERVICE = "one_on_one_service"


class AnalysisCreate(BaseModel):
    """建立分析記錄的請求 Schema"""
    content: str = Field(..., min_length=1, max_length=2000, description="Line文案內容，1-2000字")
    target_audience: TargetAudienceEnum = Field(..., description="目標受眾")
    send_scenario: SendScenarioEnum = Field(..., description="發送場景")

    @field_validator('content')
    @classmethod
    def validate_content(cls, v):
        """驗證文案內容"""
        if not v or not v.strip():
            raise ValueError('文案內容不能為空')
        
        # 簡單的惡意腳本檢查
        dangerous_patterns = ['<script', 'javascript:', 'onload=', 'onerror=']
        content_lower = v.lower()
        for pattern in dangerous_patterns:
            if pattern in content_lower:
                raise ValueError('文案內容包含不安全的內容')
        
        return v.strip()


class AnalysisResults(BaseModel):
    """分析結果 Schema"""
    attractiveness: Optional[float] = Field(None, ge=1.0, le=10.0, description="吸引力評分")
    readability: Optional[float] = Field(None, ge=1.0, le=10.0, description="可讀性評分")
    line_compatibility: Optional[float] = Field(None, ge=1.0, le=10.0, description="Line平台相容性評分")
    overall_score: Optional[float] = Field(None, ge=1.0, le=10.0, description="整體評分")
    sentiment: Optional[str] = Field(None, description="情感傾向分析")
    suggestions: Optional[List[str]] = Field(None, description="改善建議列表")


class AnalysisResponse(BaseModel):
    """分析回應 Schema"""
    analysis_id: UUID = Field(..., description="分析記錄ID")
    status: str = Field(..., description="分析狀態")
    created_at: datetime = Field(..., description="建立時間")
    results: Optional[AnalysisResults] = Field(None, description="分析結果")

    model_config = {"from_attributes": True}


class AnalysisCreateResponse(BaseModel):
    """建立分析記錄回應 Schema"""
    analysis_id: UUID = Field(..., description="分析記錄ID")
    status: str = Field(..., description="分析狀態")
    created_at: datetime = Field(..., description="建立時間")
    message: str = Field(default="分析記錄已建立，正在處理中", description="回應訊息")

    model_config = {"from_attributes": True}
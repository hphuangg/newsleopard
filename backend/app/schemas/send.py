"""
Send API Schemas

發送相關的 Pydantic Schema 定義。
"""

from pydantic import BaseModel, Field, validator
from typing import List, Optional
from datetime import datetime


class Recipient(BaseModel):
    """收件人 Schema"""
    id: str = Field(..., description="收件人ID")
    type: str = Field(..., description="收件人類型")
    name: Optional[str] = Field(None, description="收件人姓名")


class SendRequest(BaseModel):
    """發送請求 Schema"""
    content: str = Field(..., min_length=1, max_length=1000, description="訊息內容")
    channel: str = Field(..., description="發送管道")
    recipients: List[Recipient] = Field(..., min_items=1, max_items=10000, description="收件人列表")
    batch_name: Optional[str] = Field(None, max_length=255, description="批次名稱")
    send_delay: Optional[int] = Field(0, ge=0, le=3600, description="發送延遲（秒）")


class SendResponse(BaseModel):
    """發送回應 Schema"""
    success: bool = Field(..., description="是否成功")
    batch_id: Optional[str] = Field(None, description="批次ID")
    status: str = Field(..., description="發送狀態")
    total_count: int = Field(..., description="總數量")
    message: str = Field(..., description="回應訊息")
    error: Optional[str] = Field(None, description="錯誤訊息")



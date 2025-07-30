"""
Send API Schemas

發送相關的 Pydantic Schema 定義。
從 backend/app/schemas/send.py 遷移而來。
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


class Recipient(BaseModel):
    """收件人 Schema"""
    id: str = Field(..., description="收件人ID")
    type: str = Field(..., description="收件人類型")
    name: Optional[str] = Field(None, description="收件人姓名")


class SendMessageRequest(BaseModel):
    """發送請求 Schema (統一命名)"""
    content: str = Field(..., min_length=1, max_length=1000, description="訊息內容")
    channel: str = Field(..., description="發送管道")
    recipients: List[Recipient] = Field(..., min_items=1, max_items=10000, description="收件人列表")
    batch_name: Optional[str] = Field(None, max_length=255, description="批次名稱")
    send_delay: Optional[int] = Field(0, ge=0, le=3600, description="發送延遲（秒）")


class SendMessageResponse(BaseModel):
    """發送回應 Schema (統一命名)"""
    success: bool = Field(..., description="是否成功")
    batch_id: Optional[str] = Field(None, description="批次ID")
    status: str = Field(..., description="發送狀態")
    total_count: int = Field(..., description="總數量")
    message: str = Field(..., description="回應訊息")
    error: Optional[str] = Field(None, description="錯誤訊息")
    task_ids: Optional[List[str]] = Field(None, description="任務ID列表")


class BatchStatusResponse(BaseModel):
    """批次狀態回應 Schema"""
    success: bool = Field(..., description="是否成功")
    batch_id: str = Field(..., description="批次ID")
    batch_name: str = Field(..., description="批次名稱")
    total_count: int = Field(..., description="總數量")
    status_counts: Dict[str, int] = Field(..., description="狀態統計")
    batch_status: str = Field(..., description="批次狀態")
    created_at: str = Field(..., description="建立時間")
    updated_at: Optional[str] = Field(None, description="更新時間")
    error: Optional[str] = Field(None, description="錯誤訊息")


class MessageStatus(BaseModel):
    """訊息狀態 Schema"""
    id: int = Field(..., description="訊息ID")
    batch_id: str = Field(..., description="批次ID")
    channel: str = Field(..., description="發送管道")
    recipient_id: str = Field(..., description="收件人ID")
    status: str = Field(..., description="發送狀態")
    error_message: Optional[str] = Field(None, description="錯誤訊息")
    sent_at: Optional[str] = Field(None, description="發送時間")
    created_at: str = Field(..., description="建立時間")
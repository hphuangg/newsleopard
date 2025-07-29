"""
Send API Endpoints

發送相關的 FastAPI 端點實作。
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import List, Optional
from pydantic import BaseModel, Field, validator
import logging

from app.services.send_service import send_service
from app.schemas.send import SendRequest, SendResponse

logger = logging.getLogger(__name__)

router = APIRouter()


class SendMessageRequest(BaseModel):
    """發送訊息請求"""
    content: str = Field(..., min_length=1, max_length=1000, description="訊息內容")
    channel: str = Field(..., description="發送管道")
    recipients: List[dict] = Field(..., min_items=1, max_items=10000, description="收件人列表")
    batch_name: Optional[str] = Field(None, max_length=255, description="批次名稱")
    send_delay: Optional[int] = Field(0, ge=0, le=3600, description="發送延遲（秒）")
    
    @validator('channel')
    def validate_channel(cls, v):
        if v not in ['line', 'sms', 'email']:
            raise ValueError('不支援的發送管道')
        return v
    
    @validator('recipients')
    def validate_recipients(cls, v):
        for recipient in v:
            if not recipient.get('id'):
                raise ValueError('收件人ID不能為空')
            if not recipient.get('type'):
                recipient['type'] = 'default'
        return v


class SendMessageResponse(BaseModel):
    """發送訊息回應"""
    success: bool
    batch_id: Optional[str] = None
    status: str
    total_count: int
    message: str
    error: Optional[str] = None


@router.post("/send-message", response_model=SendMessageResponse)
async def send_message(
    request: SendMessageRequest,
    background_tasks: BackgroundTasks
):
    """發送訊息 API"""
    
    try:
        # 執行發送
        result = await send_service.send_message(
            content=request.content,
            channel=request.channel,
            recipients=request.recipients,
            batch_name=request.batch_name,
            send_delay=request.send_delay
        )
        
        if result["success"]:
            # 記錄成功發送
            logger.info(f"Message sent successfully. Batch ID: {result['batch_id']}")
            
            return SendMessageResponse(
                success=True,
                batch_id=result["batch_id"],
                status=result["status"],
                total_count=result["total_count"],
                message=result["message"]
            )
        else:
            # 記錄發送失敗
            logger.error(f"Message send failed: {result['error']}")
            
            return SendMessageResponse(
                success=False,
                status="failed",
                total_count=0,
                message="發送失敗",
                error=result["error"]
            )
            
    except ValueError as e:
        # 驗證錯誤
        logger.warning(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
        
    except Exception as e:
        # 系統錯誤
        logger.error(f"System error in send_message: {e}")
        raise HTTPException(status_code=500, detail="系統錯誤，請稍後再試")



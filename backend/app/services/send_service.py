"""
Send Service

統一發送服務，處理多管道訊息發送邏輯。
"""

import logging
from typing import List, Dict, Any, Optional
from uuid import uuid4

from app.crud.batch_send_record import crud_batch_send_record
from app.crud.message_send_record import crud_message_send_record

logger = logging.getLogger(__name__)


class SendService:
    """統一發送服務"""
    
    def __init__(self):
        self.supported_channels = ['line', 'sms', 'email']
    
    async def send_message(
        self,
        content: str,
        channel: str,
        recipients: List[Dict[str, Any]],
        batch_name: Optional[str] = None,
        send_delay: Optional[int] = 0
    ) -> Dict[str, Any]:
        """發送訊息
        
        Args:
            content: 訊息內容
            channel: 發送管道 (line, sms, email)
            recipients: 收件人列表
            batch_name: 批次名稱
            send_delay: 發送延遲（秒）（保留參數但不實作延遲功能）
            
        Returns:
            發送結果字典
        """
        try:
            # 驗證管道
            if channel not in self.supported_channels:
                return {
                    "success": False,
                    "error": f"不支援的發送管道: {channel}",
                    "status": "failed",
                    "total_count": 0
                }
            
            # 驗證收件人
            if not recipients:
                return {
                    "success": False,
                    "error": "收件人列表不能為空",
                    "status": "failed",
                    "total_count": 0
                }
            
            # 建立批次記錄
            batch_id = uuid4()
            total_count = len(recipients)
            
            batch_data = {
                "batch_id": batch_id,
                "batch_name": batch_name or f"{channel}_batch_{batch_id.hex[:8]}",
                "total_count": total_count,
                "success_count": 0,
                "failed_count": 0,
                "pending_count": total_count,
                "status": "pending"
            }
            
            batch_record = crud_batch_send_record.create(batch_data=batch_data)
            logger.info(f"Created batch record: {batch_record.batch_id}")
            
            # 建立個別發送記錄
            messages_data = []
            for recipient in recipients:
                message_data = {
                    "batch_id": batch_id,
                    "channel": channel,
                    "content": content,
                    "recipient_id": recipient.get("id", ""),
                    "recipient_type": recipient.get("type", "default"),
                    "status": "pending"
                }
                messages_data.append(message_data)
            
            message_records = crud_message_send_record.create_batch(
                messages_data=messages_data
            )
            logger.info(f"Created {len(message_records)} message records")
            
            return {
                "success": True,
                "batch_id": str(batch_id),
                "status": "accepted",
                "total_count": total_count,
                "message": "發送請求已接受，正在處理中"
            }
            
        except Exception as e:
            logger.error(f"Send message error: {e}")
            return {
                "success": False,
                "error": f"發送失敗: {str(e)}",
                "status": "failed",
                "total_count": 0
            }
    


# 建立全域實例
send_service = SendService()
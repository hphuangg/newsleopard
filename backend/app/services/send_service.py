"""
Send Service

統一發送服務，處理多管道訊息發送邏輯。
現在整合 AWS SQS 進行非同步訊息處理。
"""

import logging
from typing import List, Dict, Any, Optional
from uuid import uuid4

from app.crud.batch_send_record import crud_batch_send_record
from app.crud.message_send_record import crud_message_send_record
from app.services.sqs_queue_manager import sqs_queue_manager

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
            
            # 推送到 SQS 佇列
            queue_result = await self._enqueue_messages(
                batch_id=batch_id,
                channel=channel,
                content=content,
                message_records=message_records,
                recipients=recipients
            )
            
            if not queue_result['success']:
                logger.error(f"Failed to enqueue messages: {queue_result['error']}")
                return {
                    "success": False,
                    "error": f"佇列推送失敗: {queue_result['error']}",
                    "status": "failed",
                    "batch_id": str(batch_id),
                    "total_count": total_count
                }
            
            return {
                "success": True,
                "batch_id": str(batch_id),
                "status": "queued",
                "total_count": total_count,
                "message": f"發送請求已加入佇列，{queue_result['queued_count']} 個任務已推送",
                "task_ids": queue_result['task_ids']
            }
            
        except Exception as e:
            logger.error(f"Send message error: {e}")
            return {
                "success": False,
                "error": f"發送失敗: {str(e)}",
                "status": "failed",
                "total_count": 0
            }
    
    async def _enqueue_messages(
        self,
        batch_id: str,
        channel: str,
        content: str,
        message_records: List[Any],
        recipients: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """推送訊息到 SQS 佇列"""
        try:
            task_ids = []
            
            # 決定佇列策略
            if len(recipients) <= 5:
                # 小批次：推送到單一訊息佇列
                for i, message_record in enumerate(message_records):
                    recipient = recipients[i]
                    
                    message_data = {
                        'type': 'send_message',
                        'batch_id': str(batch_id),
                        'message_id': message_record.id,
                        'channel': channel,
                        'content': content,
                        'recipient': recipient,
                        'created_at': message_record.created_at.isoformat()
                    }
                    
                    task_id = await sqs_queue_manager.send_message(
                        queue_name='send_queue',
                        message_data=message_data
                    )
                    
                    if task_id:
                        task_ids.append(task_id)
                        logger.debug(f"Enqueued single message {message_record.id}: {task_id}")
                    else:
                        logger.error(f"Failed to enqueue message {message_record.id}")
            
            else:
                # 大批次：推送到批次佇列
                # 準備批次資料
                batch_recipients = []
                for i, recipient in enumerate(recipients):
                    batch_recipients.append({
                        **recipient,
                        'message_id': message_records[i].id
                    })
                
                batch_message_data = {
                    'type': 'batch_send',
                    'batch_id': str(batch_id),
                    'channel': channel,
                    'content': content,
                    'recipients': batch_recipients,
                    'total_count': len(batch_recipients)
                }
                
                task_id = await sqs_queue_manager.send_message(
                    queue_name='batch_queue',
                    message_data=batch_message_data
                )
                
                if task_id:
                    task_ids.append(task_id)
                    logger.info(f"Enqueued batch message {batch_id}: {task_id}")
                else:
                    logger.error(f"Failed to enqueue batch message {batch_id}")
            
            if not task_ids:
                return {
                    'success': False,
                    'error': 'No messages were successfully enqueued',
                    'queued_count': 0,
                    'task_ids': []
                }
            
            return {
                'success': True,
                'queued_count': len(task_ids),
                'task_ids': task_ids,
                'queue_strategy': 'single' if len(recipients) <= 5 else 'batch'
            }
            
        except Exception as e:
            logger.error(f"Error enqueueing messages: {e}")
            return {
                'success': False,
                'error': str(e),
                'queued_count': 0,
                'task_ids': []
            }
    
    async def get_send_status(self, batch_id: str) -> Dict[str, Any]:
        """取得發送狀態"""
        try:
            # 取得批次記錄
            batch_record = crud_batch_send_record.get_by_batch_id(batch_id)
            if not batch_record:
                return {
                    'success': False,
                    'error': f'找不到批次記錄: {batch_id}'
                }
            
            # 取得訊息記錄
            message_records = crud_message_send_record.get_by_batch_id(batch_id)
            
            # 統計狀態
            status_counts = {}
            for record in message_records:
                status = record.status
                status_counts[status] = status_counts.get(status, 0) + 1
            
            return {
                'success': True,
                'batch_id': batch_id,
                'batch_name': batch_record.batch_name,
                'total_count': batch_record.total_count,
                'status_counts': status_counts,
                'batch_status': batch_record.status,
                'created_at': batch_record.created_at.isoformat(),
                'updated_at': batch_record.updated_at.isoformat() if batch_record.updated_at else None
            }
            
        except Exception as e:
            logger.error(f"Error getting send status: {e}")
            return {
                'success': False,
                'error': str(e)
            }


# 建立全域實例
send_service = SendService()
"""
統一訊息處理器

處理來自 SQS 佇列的發送任務，
從 backend/app/workers/sqs_worker.py 重構而來。
"""

import asyncio
import logging
import random
from typing import Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class MessageHandler:
    """統一訊息處理器"""
    
    def __init__(self):
        pass
        
    async def handle_message(self, queue_name: str, message: Dict[str, Any]) -> bool:
        """
        處理訊息
        
        Args:
            queue_name: 佇列名稱
            message: 訊息內容
            
        Returns:
            True if processed successfully, False otherwise
        """
        try:
            message_id = message['message_id']
            body = message['body']
            
            logger.info(f"Processing message {message_id} from {queue_name}")
            
            if queue_name == 'send_queue':
                return await self._handle_single_send(body)
            elif queue_name == 'batch_queue':
                return await self._handle_batch_send(body)
            else:
                logger.error(f"Unknown queue: {queue_name}")
                return False
                
        except Exception as e:
            logger.error(f"Error handling message: {e}")
            return False
            
    async def _handle_single_send(self, message_data: Dict[str, Any]) -> bool:
        """處理單一發送 (從原 SQS Worker 遷移)"""
        try:
            # 提取訊息資料
            batch_id = message_data.get('batch_id')
            message_id = message_data.get('message_id')
            channel = message_data.get('channel')
            content = message_data.get('content')
            recipient = message_data.get('recipient')
            
            logger.info(f"Sending single message: batch_id={batch_id}, message_id={message_id}, channel={channel}")
            
            # TODO: 整合 TASK-04 發送管道抽象層
            # 目前模擬發送
            await asyncio.sleep(0.5)  # 模擬發送延遲
            
            # 模擬發送結果
            success_rate = 0.9  # 90% 成功率
            is_success = random.random() < success_rate
            
            if is_success:
                # TODO: 更新資料庫記錄為成功 (使用 shared models)
                logger.info(f"Message {message_id} sent successfully")
                return True
            else:
                # TODO: 更新資料庫記錄為失敗
                logger.warning(f"Message {message_id} send failed")
                return False
                
        except Exception as e:
            logger.error(f"Error in _handle_single_send: {e}")
            return False
    
    async def _handle_batch_send(self, message_data: Dict[str, Any]) -> bool:
        """處理批次發送 (從原 SQS Worker 遷移)"""
        try:
            batch_id = message_data.get('batch_id')
            channel = message_data.get('channel')
            content = message_data.get('content')
            recipients = message_data.get('recipients', [])
            
            logger.info(f"Sending batch message: batch_id={batch_id}, channel={channel}, recipients={len(recipients)}")
            
            # TODO: 實際的批次發送邏輯
            # 目前模擬批次發送
            results = []
            for recipient in recipients:
                await asyncio.sleep(0.1)  # 模擬每個發送的延遲
                
                # 模擬發送結果
                is_success = random.random() < 0.85  # 85% 成功率
                
                result = {
                    'recipient_id': recipient.get('id'),
                    'message_id': recipient.get('message_id'),
                    'success': is_success,
                    'status': 'sent' if is_success else 'failed',
                    'error': None if is_success else 'Simulated batch send failure'
                }
                results.append(result)
            
            # 統計結果
            success_count = sum(1 for r in results if r['success'])
            failed_count = len(results) - success_count
            
            logger.info(f"Batch {batch_id} completed: {success_count} success, {failed_count} failed")
            
            # TODO: 更新批次統計 (使用 shared models)
            
            return True  # 批次處理完成視為成功
            
        except Exception as e:
            logger.error(f"Error in _handle_batch_send: {e}")
            return False
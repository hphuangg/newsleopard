"""
統一訊息處理器

處理來自 SQS 佇列的發送任務，
從 backend/app/workers/sqs_worker.py 重構而來。
"""

import asyncio
import logging
import random
import sys
from pathlib import Path
from typing import Dict, Any
from datetime import datetime

# 添加根目錄到路徑以使用 shared 模組
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from app.channels.line_bot import LineBotChannel
from shared.channels.exceptions import ChannelConfigurationError

logger = logging.getLogger(__name__)


class MessageHandler:
    """統一訊息處理器"""
    
    def __init__(self):
        self.line_channel = None
        self._init_channels()
    
    def _init_channels(self):
        """初始化發送管道"""
        try:
            self.line_channel = LineBotChannel()
            logger.info("Line Bot channel initialized successfully")
        except ChannelConfigurationError as e:
            logger.warning(f"Line Bot channel not available: {e}")
            self.line_channel = None
        except Exception as e:
            logger.error(f"Error initializing Line Bot channel: {e}")
            self.line_channel = None
        
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
            
            logger.info(f"📨 Processing message {message_id} from {queue_name}")
            logger.debug(f"Message body: {body}")
            
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
        """處理單一發送 - 整合 Line Bot 真實發送"""
        try:
            # 提取訊息資料
            batch_id = message_data.get('batch_id')
            message_id = message_data.get('message_id')
            channel = message_data.get('channel', 'line')  # 預設為 line
            content = message_data.get('content')
            recipient = message_data.get('recipient')
            recipient_id = recipient.get('id') if isinstance(recipient, dict) else recipient
            
            logger.info(f"📤 Sending single message: batch_id={batch_id}, message_id={message_id}, channel={channel}")
            logger.debug(f"Content: {content}, Recipient: {recipient}, Recipient ID: {recipient_id}")
            
            # 根據管道類型處理發送
            if channel == 'line':
                return await self._send_via_line(content, recipient_id, message_id)
            else:
                # 其他管道先使用模擬發送
                logger.warning(f"Channel {channel} not implemented, using simulation")
                return await self._simulate_send(content, recipient_id, message_id)
                
        except Exception as e:
            logger.error(f"Error in _handle_single_send: {e}")
            return False
    
    async def _send_via_line(self, content: str, recipient: str, message_id: str) -> bool:
        """透過 Line Bot 發送訊息"""
        try:
            logger.info(f"🔍 Starting Line Bot send process for message {message_id}")
            logger.debug(f"Line channel object: {self.line_channel}")
            
            if not self.line_channel:
                logger.error(f"Line channel not available for message {message_id}")
                return False
            
            # 檢查管道可用性
            logger.info(f"🔍 Checking Line channel availability...")
            is_available = await self.line_channel.is_available()
            logger.info(f"Line channel available: {is_available}")
            
            if not is_available:
                logger.error(f"Line channel is not available for message {message_id}")
                return False
            
            logger.info(f"📱 Sending via Line Bot: message_id={message_id}, recipient={recipient}")
            
            # 使用 Line Bot 發送訊息
            result = await self.line_channel.send_message(content, recipient)
            
            logger.info(f"Line Bot send result status: {result.status.value}")
            logger.debug(f"Line Bot send result: {result}")
            
            if result.status.value == 'success':
                logger.info(f"✅ Line message {message_id} sent successfully")
                logger.debug(f"Line response: {result.response_data}")
                return True
            else:
                logger.warning(f"❌ Line message {message_id} failed: {result.error_message}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending via Line Bot for message {message_id}: {e}")
            return False
    
    async def _simulate_send(self, content: str, recipient: str, message_id: str) -> bool:
        """模擬發送 (用於非 Line 管道)"""
        try:
            logger.debug(f"⏳ Simulating send for message {message_id} to {recipient}")
            logger.debug(f"Content: {content}")
            await asyncio.sleep(0.1)  # 模擬發送延遲
            
            # 模擬發送結果
            success_rate = 0.9  # 90% 成功率
            is_success = random.random() < success_rate
            
            if is_success:
                logger.info(f"✅ Simulated message {message_id} sent successfully")
                return True
            else:
                logger.warning(f"❌ Simulated message {message_id} send failed")
                return False
                
        except Exception as e:
            logger.error(f"Error in _simulate_send: {e}")
            return False
    
    async def _handle_batch_send(self, message_data: Dict[str, Any]) -> bool:
        """處理批次發送 (從原 SQS Worker 遷移)"""
        try:
            batch_id = message_data.get('batch_id')
            channel = message_data.get('channel')
            content = message_data.get('content')
            recipients = message_data.get('recipients', [])
            
            logger.info(f"Sending batch message: batch_id={batch_id}, channel={channel}, recipients={len(recipients)}")
            logger.debug(f"Batch content: {content}")
            
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
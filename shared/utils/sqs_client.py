"""
共用 SQS 客戶端

提供 Backend 和 Worker 共用的 SQS 操作功能。
從 backend/app/services/sqs_queue_manager.py 重構而來。
"""

import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from botocore.exceptions import ClientError

from shared.config.settings import settings
from shared.utils.sqs_config import SQSConfig

logger = logging.getLogger(__name__)


class SQSClient:
    """共用 SQS 客戶端"""
    
    def __init__(self):
        self.sqs_config = SQSConfig()
        self.sqs_client = self.sqs_config.get_sqs_client()
        self.queue_urls = self.sqs_config.get_queue_urls()
        
    async def send_message(self, queue_name: str, message_data: Dict[str, Any]) -> Optional[str]:
        """
        發送訊息到指定佇列
        
        Args:
            queue_name: 佇列名稱 ('send_queue', 'batch_queue')
            message_data: 訊息內容
            
        Returns:
            Message ID if successful, None if failed
        """
        try:
            if queue_name not in self.queue_urls:
                logger.error(f"Unknown queue name: {queue_name}")
                return None
                
            queue_url = self.queue_urls[queue_name]
            
            # 準備訊息內容
            message_body = json.dumps(message_data, ensure_ascii=False, default=str)
            
            # 基本發送參數
            send_params = {
                'QueueUrl': queue_url,
                'MessageBody': message_body,
                'MessageAttributes': {
                    'queue_name': {
                        'StringValue': queue_name,
                        'DataType': 'String'
                    },
                    'timestamp': {
                        'StringValue': datetime.utcnow().isoformat(),
                        'DataType': 'String'
                    },
                    'message_type': {
                        'StringValue': message_data.get('type', 'send_message'),
                        'DataType': 'String'
                    }
                }
            }
            
            # 發送訊息
            response = self.sqs_client.send_message(**send_params)
            message_id = response.get('MessageId')
            
            logger.info(f"Message sent to {queue_name}: {message_id}")
            return message_id
            
        except ClientError as e:
            logger.error(f"Failed to send message to {queue_name}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error sending message to {queue_name}: {e}")
            return None
    
    async def receive_messages(self, queue_name: str, max_messages: int = 1,
                              wait_time_seconds: int = 20) -> List[Dict[str, Any]]:
        """
        從指定佇列接收訊息
        
        Args:
            queue_name: 佇列名稱
            max_messages: 最大接收訊息數 (1-10)
            wait_time_seconds: 長輪詢等待時間
            
        Returns:
            List of messages with parsed content
        """
        try:
            if queue_name not in self.queue_urls:
                logger.error(f"Unknown queue name: {queue_name}")
                return []
                
            queue_url = self.queue_urls[queue_name]
            
            # 接收訊息
            response = self.sqs_client.receive_message(
                QueueUrl=queue_url,
                MaxNumberOfMessages=min(max_messages, 10),
                WaitTimeSeconds=wait_time_seconds,
                MessageAttributeNames=['All']
            )
            
            messages = response.get('Messages', [])
            if not messages:
                return []
            
            # 解析訊息
            parsed_messages = []
            for message in messages:
                try:
                    # 解析訊息內容
                    message_body = json.loads(message['Body'])
                    
                    parsed_message = {
                        'message_id': message['MessageId'],
                        'receipt_handle': message['ReceiptHandle'],
                        'body': message_body,
                        'attributes': message.get('MessageAttributes', {}),
                        'received_at': datetime.utcnow().isoformat()
                    }
                    
                    parsed_messages.append(parsed_message)
                    
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse message body: {e}")
                    continue
            
            logger.debug(f"Received {len(parsed_messages)} messages from {queue_name}")
            return parsed_messages
            
        except ClientError as e:
            logger.error(f"Failed to receive messages from {queue_name}: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error receiving messages from {queue_name}: {e}")
            return []
    
    async def delete_message(self, queue_name: str, receipt_handle: str) -> bool:
        """
        刪除已處理的訊息
        
        Args:
            queue_name: 佇列名稱
            receipt_handle: 訊息接收控制碼
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if queue_name not in self.queue_urls:
                logger.error(f"Unknown queue name: {queue_name}")
                return False
                
            queue_url = self.queue_urls[queue_name]
            
            # 刪除訊息
            self.sqs_client.delete_message(
                QueueUrl=queue_url,
                ReceiptHandle=receipt_handle
            )
            
            logger.debug(f"Message deleted from {queue_name}")
            return True
            
        except ClientError as e:
            logger.error(f"Failed to delete message from {queue_name}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error deleting message from {queue_name}: {e}")
            return False
    
    async def test_connection(self) -> bool:
        """測試 SQS 連接"""
        try:
            for queue_name in self.queue_urls.keys():
                await self.receive_messages(queue_name, max_messages=1, wait_time_seconds=0)
            return True
        except Exception as e:
            logger.error(f"SQS connection test failed: {e}")
            return False
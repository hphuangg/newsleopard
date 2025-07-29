"""
SQS 佇列管理器 (簡化版)

只保留核心的訊息發送和接收功能。
"""

import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from botocore.exceptions import ClientError

from app.core.sqs_config import sqs_config

logger = logging.getLogger(__name__)


class SQSQueueManager:
    """SQS 佇列管理器 (簡化版)"""
    
    def __init__(self):
        self.sqs_client = sqs_config.get_sqs_client()
        self.queue_urls = sqs_config.get_queue_urls()
        
    async def send_message(self, queue_name: str, message_data: Dict[str, Any], 
                          message_group_id: Optional[str] = None,
                          message_deduplication_id: Optional[str] = None) -> Optional[str]:
        """
        發送訊息到指定佇列
        
        Args:
            queue_name: 佇列名稱 ('send_queue', 'batch_queue')
            message_data: 訊息內容
            message_group_id: FIFO 佇列群組 ID (可選)
            message_deduplication_id: FIFO 佇列去重 ID (可選)
            
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
            
            # 基本送訊參數
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
            
            # FIFO 佇列支援
            if message_group_id:
                send_params['MessageGroupId'] = message_group_id
            if message_deduplication_id:
                send_params['MessageDeduplicationId'] = message_deduplication_id
            
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
            List of received messages
        """
        try:
            if queue_name not in self.queue_urls:
                logger.error(f"Unknown queue name: {queue_name}")
                return []
                
            queue_url = self.queue_urls[queue_name]
            
            response = self.sqs_client.receive_message(
                QueueUrl=queue_url,
                MaxNumberOfMessages=min(max_messages, 10),
                WaitTimeSeconds=wait_time_seconds,
                MessageAttributeNames=['All'],
                AttributeNames=['All']
            )
            
            messages = response.get('Messages', [])
            
            # 解析訊息內容
            parsed_messages = []
            for message in messages:
                try:
                    message_body = json.loads(message['Body'])
                    parsed_message = {
                        'message_id': message['MessageId'],
                        'receipt_handle': message['ReceiptHandle'],
                        'body': message_body,
                        'attributes': message.get('Attributes', {}),
                        'message_attributes': message.get('MessageAttributes', {}),
                        'queue_name': queue_name
                    }
                    parsed_messages.append(parsed_message)
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse message body: {e}")
                    continue
            
            if parsed_messages:
                logger.info(f"Received {len(parsed_messages)} messages from {queue_name}")
            
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
            receipt_handle: 訊息接收句柄
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if queue_name not in self.queue_urls:
                logger.error(f"Unknown queue name: {queue_name}")
                return False
                
            queue_url = self.queue_urls[queue_name]
            
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


# 全域佇列管理器實例
sqs_queue_manager = SQSQueueManager()
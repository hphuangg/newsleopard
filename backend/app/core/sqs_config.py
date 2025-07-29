"""
AWS SQS 配置管理器

設定 SQS 客戶端和佇列配置，支援 LocalStack 本地開發。
"""

import boto3
import logging
from typing import Optional, Dict
from botocore.exceptions import ClientError, NoCredentialsError
from app.core.config import settings

logger = logging.getLogger(__name__)


class SQSConfig:
    """AWS SQS 配置管理器"""
    
    def __init__(self):
        self.region = settings.aws.region
        self.endpoint_url = settings.aws.sqs_endpoint_url
        self._client = None
        
    def get_sqs_client(self):
        """建立 SQS 客戶端 (單例模式)"""
        if self._client is None:
            try:
                client_config = {
                    'region_name': self.region,
                    'aws_access_key_id': settings.aws.access_key_id,
                    'aws_secret_access_key': settings.aws.secret_access_key,
                }
                
                # LocalStack 支援
                if self.endpoint_url:
                    client_config['endpoint_url'] = self.endpoint_url
                    logger.info(f"Using LocalStack SQS endpoint: {self.endpoint_url}")
                
                self._client = boto3.client('sqs', **client_config)
                logger.info(f"SQS client initialized for region: {self.region}")
                
            except NoCredentialsError:
                logger.error("AWS credentials not found. Please set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY")
                raise
            except Exception as e:
                logger.error(f"Failed to initialize SQS client: {e}")
                raise
                
        return self._client
    
    def get_queue_urls(self) -> Dict[str, str]:
        """取得佇列 URL 配置"""
        return {
            'send_queue': settings.sqs.send_queue_url,
            'batch_queue': settings.sqs.batch_queue_url, 
            'send_dlq': settings.sqs.send_dlq_url,
            'batch_dlq': settings.sqs.batch_dlq_url,
        }
    
    def validate_configuration(self) -> bool:
        """驗證 SQS 配置是否正確"""
        try:
            client = self.get_sqs_client()
            queue_urls = self.get_queue_urls()
            
            # 檢查每個佇列是否存在
            for queue_name, queue_url in queue_urls.items():
                try:
                    response = client.get_queue_attributes(
                        QueueUrl=queue_url,
                        AttributeNames=['QueueArn']
                    )
                    logger.info(f"Queue {queue_name} is accessible: {queue_url}")
                except ClientError as e:
                    logger.error(f"Queue {queue_name} is not accessible: {queue_url}, Error: {e}")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"SQS configuration validation failed: {e}")
            return False
    
    def get_queue_attributes(self, queue_url: str) -> Optional[Dict]:
        """取得佇列屬性資訊"""
        try:
            client = self.get_sqs_client()
            response = client.get_queue_attributes(
                QueueUrl=queue_url,
                AttributeNames=['All']
            )
            return response.get('Attributes', {})
        except Exception as e:
            logger.error(f"Failed to get queue attributes for {queue_url}: {e}")
            return None


# 全域 SQS 配置實例
sqs_config = SQSConfig()
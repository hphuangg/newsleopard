"""
共用 SQS 配置

提供 Backend 和 Worker 共用的 SQS 配置管理。
從 backend/app/core/sqs_config.py 重構而來。
"""

import boto3
from typing import Dict
from shared.config.settings import settings


class SQSConfig:
    """SQS 配置管理器"""
    
    def __init__(self):
        self.region = settings.aws.region
        self.endpoint_url = settings.aws.sqs_endpoint_url
        
    def get_sqs_client(self):
        """建立 SQS 客戶端"""
        client_config = {
            'region_name': self.region,
            'aws_access_key_id': settings.aws.access_key_id,
            'aws_secret_access_key': settings.aws.secret_access_key,
        }
        
        # LocalStack 支援
        if self.endpoint_url:
            client_config['endpoint_url'] = self.endpoint_url
            
        return boto3.client('sqs', **client_config)
    
    def get_queue_urls(self) -> Dict[str, str]:
        """取得佇列 URL 配置"""
        return {
            'send_queue': settings.sqs.send_queue_url,
            'batch_queue': settings.sqs.batch_queue_url,
            'send_dlq': settings.sqs.send_dlq_url,
            'batch_dlq': settings.sqs.batch_dlq_url,
        }
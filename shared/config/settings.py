"""
統一配置管理

提供 Backend 和 Worker 共用的配置設定。
"""

from pydantic import Field
from pydantic_settings import BaseSettings
from typing import Optional


class DatabaseSettings(BaseSettings):
    """資料庫設定"""
    server: str = Field(default="localhost", alias="POSTGRES_SERVER")
    user: str = Field(default="postgres", alias="POSTGRES_USER") 
    password: str = Field(default="postgres", alias="POSTGRES_PASSWORD")
    db: str = Field(default="backend", alias="POSTGRES_DB")
    port: int = Field(default=5432, alias="POSTGRES_PORT")
    
    @property
    def url(self) -> str:
        return f"postgresql://{self.user}:{self.password}@{self.server}:{self.port}/{self.db}"
    
    model_config = {"env_file": ".env", "case_sensitive": False, "extra": "ignore"}


class AWSSettings(BaseSettings):
    """AWS 相關設定"""
    access_key_id: str = Field(default="test", alias="AWS_ACCESS_KEY_ID")
    secret_access_key: str = Field(default="test", alias="AWS_SECRET_ACCESS_KEY")
    region: str = Field(default="us-east-1", alias="AWS_REGION")
    sqs_endpoint_url: Optional[str] = Field(default="http://localhost:4566", alias="AWS_SQS_ENDPOINT_URL")
    
    model_config = {"env_file": ".env", "case_sensitive": False, "extra": "ignore"}


class SQSSettings(BaseSettings):  
    """SQS 佇列設定"""
    send_queue_url: str = Field(default="http://sqs.us-east-1.localhost.localstack.cloud:4566/000000000000/send-queue", alias="SQS_SEND_QUEUE_URL")
    batch_queue_url: str = Field(default="http://sqs.us-east-1.localhost.localstack.cloud:4566/000000000000/batch-queue", alias="SQS_BATCH_QUEUE_URL")  
    send_dlq_url: str = Field(default="http://sqs.us-east-1.localhost.localstack.cloud:4566/000000000000/send-dlq", alias="SQS_SEND_DLQ_URL")
    batch_dlq_url: str = Field(default="http://sqs.us-east-1.localhost.localstack.cloud:4566/000000000000/batch-dlq", alias="SQS_BATCH_DLQ_URL")
    
    # 佇列配置
    message_retention_period: int = Field(default=1209600)  # 14天
    visibility_timeout: int = Field(default=300)  # 5分鐘
    max_receive_count: int = Field(default=3)  # DLQ 重試次數
    
    model_config = {"env_file": ".env", "case_sensitive": False, "extra": "ignore"}


class SharedSettings(BaseSettings):
    """共用主要設定"""
    project_name: str = Field(default="NewsLeopard", alias="PROJECT_NAME")
    debug: bool = Field(default=False, alias="DEBUG")
    api_v1_str: str = Field(default="/api/v1", alias="API_V1_STR")
    
    model_config = {
        "env_file": ".env",
        "case_sensitive": False,
        "extra": "ignore"
    }
    
    @property
    def database(self) -> DatabaseSettings:
        """延遲載入資料庫設定"""
        if not hasattr(self, '_database'):
            self._database = DatabaseSettings()
        return self._database
    
    @property 
    def aws(self) -> AWSSettings:
        """延遲載入 AWS 設定"""
        if not hasattr(self, '_aws'):
            self._aws = AWSSettings()
        return self._aws
    
    @property
    def sqs(self) -> SQSSettings:
        """延遲載入 SQS 設定"""
        if not hasattr(self, '_sqs'):
            self._sqs = SQSSettings()
        return self._sqs


# 全域設定實例
settings = SharedSettings()
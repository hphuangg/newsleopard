from typing import Optional, Dict, Any
from pydantic import Field
from pydantic_settings import BaseSettings


class DatabaseSettings(BaseSettings):
    """資料庫配置"""
    server: str = Field(default="localhost", alias="POSTGRES_SERVER")
    user: str = Field(default="postgres", alias="POSTGRES_USER")
    password: str = Field(default="postgres", alias="POSTGRES_PASSWORD")
    database: str = Field(default="backend", alias="POSTGRES_DB")
    port: int = Field(default=5432, alias="POSTGRES_PORT")
    
    model_config = {"env_file": ".env", "case_sensitive": False, "extra": "ignore"}
    
    @property
    def url(self) -> str:
        return f"postgresql://{self.user}:{self.password}@{self.server}:{self.port}/{self.database}"


class AIProviderSettings(BaseSettings):
    """AI 提供商基礎配置"""
    max_retries: int = 3
    timeout: int = 30
    max_tokens: int = 1000
    temperature: float = 0.3
    
    model_config = {"extra": "ignore"}


class OpenAISettings(AIProviderSettings):
    """OpenAI 配置"""
    api_key: Optional[str] = Field(default=None, alias="OPENAI_API_KEY")
    model: str = Field(default="gpt-4o-mini", alias="OPENAI_MODEL")
    max_tokens: int = Field(default=1000, alias="OPENAI_MAX_TOKENS")
    temperature: float = Field(default=0.3, alias="OPENAI_TEMPERATURE")
    organization: Optional[str] = Field(default=None, alias="OPENAI_ORGANIZATION")
    
    model_config = {"env_file": ".env", "case_sensitive": False, "extra": "ignore"}


class ClaudeSettings(AIProviderSettings):
    """Claude 配置"""
    api_key: Optional[str] = Field(default=None, alias="CLAUDE_API_KEY")
    model: str = Field(default="claude-3-haiku-20240307", alias="CLAUDE_MODEL")
    max_tokens: int = Field(default=1000, alias="CLAUDE_MAX_TOKENS")
    
    model_config = {"env_file": ".env", "case_sensitive": False, "extra": "ignore"}


class AISettings(BaseSettings):
    """AI 服務總配置"""
    default_provider: str = Field(default="openai", alias="AI_DEFAULT_PROVIDER")
    openai: OpenAISettings = OpenAISettings()
    claude: ClaudeSettings = ClaudeSettings()
    
    # 全域 AI 設定
    analysis_timeout: int = Field(default=60, alias="AI_ANALYSIS_TIMEOUT")
    concurrent_requests: int = Field(default=5, alias="AI_CONCURRENT_REQUESTS")
    
    model_config = {"env_file": ".env", "case_sensitive": False, "extra": "ignore"}


class AWSSettings(BaseSettings):
    """AWS 相關設定"""
    access_key_id: str = Field(alias="AWS_ACCESS_KEY_ID")
    secret_access_key: str = Field(alias="AWS_SECRET_ACCESS_KEY")
    region: str = Field(default="ap-northeast-1", alias="AWS_REGION")
    sqs_endpoint_url: Optional[str] = Field(default=None, alias="AWS_SQS_ENDPOINT_URL")
    
    model_config = {"env_file": ".env", "case_sensitive": False, "extra": "ignore"}


class SQSSettings(BaseSettings):  
    """SQS 佇列設定"""
    send_queue_url: str = Field(alias="SQS_SEND_QUEUE_URL")
    batch_queue_url: str = Field(alias="SQS_BATCH_QUEUE_URL")  
    send_dlq_url: str = Field(alias="SQS_SEND_DLQ_URL")
    batch_dlq_url: str = Field(alias="SQS_BATCH_DLQ_URL")
    
    # 佇列配置
    message_retention_period: int = Field(default=1209600)  # 14天
    visibility_timeout: int = Field(default=300)  # 5分鐘
    max_receive_count: int = Field(default=3)  # DLQ 重試次數
    
    model_config = {"env_file": ".env", "case_sensitive": False, "extra": "ignore"}


class Settings(BaseSettings):
    """主要應用程式配置"""
    project_name: str = Field(default="Backend API", alias="PROJECT_NAME")
    api_v1_str: str = Field(default="/api/v1", alias="API_V1_STR")
    debug: bool = Field(default=False, alias="DEBUG")
    
    # 子配置
    database: DatabaseSettings = DatabaseSettings()
    ai: AISettings = AISettings()
    aws: AWSSettings = AWSSettings()
    sqs: SQSSettings = SQSSettings()
    
    model_config = {
        "env_file": ".env",
        "case_sensitive": False,
        "extra": "ignore"
    }


settings = Settings()
"""
Backend API 配置

使用 shared 模組的基礎配置，並添加 Backend 特有的 AI 設定。
"""

import sys
from pathlib import Path
from typing import Optional, Dict, Any
from pydantic import Field
from pydantic_settings import BaseSettings

# 添加 shared 模組到路徑
current_file = Path(__file__).resolve()
backend_dir = current_file.parent.parent.parent  # backend/app/core -> backend
project_root = backend_dir.parent  # backend -> project root
shared_dir = project_root / "shared"
sys.path.insert(0, str(project_root))

from shared.config.settings import SharedSettings


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


class BackendSettings(SharedSettings):
    """Backend 特有設定，繼承 SharedSettings"""
    
    # AI 設定 (Backend 特有)
    ai: AISettings = AISettings()
    
    model_config = {
        "env_file": ".env",
        "case_sensitive": False,
        "extra": "ignore"
    }


# Backend 設定實例 (保持向後相容)
settings = BackendSettings()
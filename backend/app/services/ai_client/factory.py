"""AI 客戶端工廠"""

from typing import Dict, Type
from .base import AIClientBase
from .openai_client import OpenAIClient
from .claude_client import ClaudeClient
from app.core.config import settings


class AIClientFactory:
    """AI 客戶端工廠"""
    
    _clients: Dict[str, Type[AIClientBase]] = {
        "openai": OpenAIClient,
        "claude": ClaudeClient
    }
    
    @classmethod
    def create_client(cls, provider: str) -> AIClientBase:
        """建立指定的 AI 客戶端"""
        if provider not in cls._clients:
            available_providers = list(cls._clients.keys())
            raise ValueError(f"不支援的 AI 提供商: {provider}，可用選項: {available_providers}")
        
        client_class = cls._clients[provider]
        return client_class()
    
    @classmethod
    def register_client(cls, provider: str, client_class: Type[AIClientBase]):
        """註冊新的 AI 客戶端"""
        cls._clients[provider] = client_class
    
    @classmethod
    def get_available_providers(cls) -> list[str]:
        """獲取所有可用的 AI 提供商"""
        return list(cls._clients.keys())


def create_ai_client(provider: str = None) -> AIClientBase:
    """建立 AI 客戶端實例"""
    if provider is None:
        provider = settings.ai.default_provider
    
    return AIClientFactory.create_client(provider)


def get_default_ai_client() -> AIClientBase:
    """獲取預設的 AI 客戶端"""
    return create_ai_client()
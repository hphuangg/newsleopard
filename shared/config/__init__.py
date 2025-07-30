"""
共用配置管理
"""

from .settings import settings, DatabaseSettings, AWSSettings, SQSSettings, SharedSettings

__all__ = ["settings", "DatabaseSettings", "AWSSettings", "SQSSettings", "SharedSettings"]
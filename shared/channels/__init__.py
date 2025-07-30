"""
共用發送管道模組

提供跨 Backend 和 Worker 的發送管道抽象介面。
"""

from .base import MessageChannel, SendResult, SendStatus, RateLimit
from .exceptions import (
    ChannelError,
    ChannelNotFoundError,
    ChannelUnavailableError,
    RateLimitExceededError,
    InvalidRecipientError,
    ChannelConfigurationError
)

__all__ = [
    # 抽象介面和資料結構
    'MessageChannel',
    'SendResult', 
    'SendStatus',
    'RateLimit',
    # 例外類別
    'ChannelError',
    'ChannelNotFoundError',
    'ChannelUnavailableError', 
    'RateLimitExceededError',
    'InvalidRecipientError',
    'ChannelConfigurationError'
]
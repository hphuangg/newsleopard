"""
Worker 發送管道實作

實作各種具體的發送管道、工廠模式和管道管理器。
"""

from .line_bot import LineBotChannel
from .factory import ChannelFactory
from .manager import ChannelManager

__all__ = [
    'LineBotChannel',
    'ChannelFactory',
    'ChannelManager'
]
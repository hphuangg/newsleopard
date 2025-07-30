"""
共用 Pydantic 模型
"""

from .send import SendMessageRequest, SendMessageResponse, BatchStatusResponse

__all__ = ["SendMessageRequest", "SendMessageResponse", "BatchStatusResponse"]
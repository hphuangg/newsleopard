"""
Send API Schemas (Backend 引用)

使用 shared 模組的發送相關 Schema。
"""

import sys
from pathlib import Path

# 添加 shared 模組到路徑
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "shared"))

from shared.schemas.send import (
    Recipient, 
    SendMessageRequest, 
    SendMessageResponse, 
    BatchStatusResponse,
    MessageStatus
)

# 保持向後相容的別名
SendRequest = SendMessageRequest
SendResponse = SendMessageResponse

# 重新匯出供 Backend 使用
__all__ = [
    "Recipient", 
    "SendMessageRequest", 
    "SendMessageResponse", 
    "BatchStatusResponse",
    "MessageStatus",
    "SendRequest",  # 向後相容
    "SendResponse"  # 向後相容
]



"""
MessageSendRecord Model (Backend 引用)

使用 shared 模組的個別發送記錄模型。
"""

import sys
from pathlib import Path

# 添加 shared 模組到路徑
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "shared"))

from shared.models.message_send_record import MessageSendRecord

# 重新匯出供 Backend 使用
__all__ = ["MessageSendRecord"]
"""
BatchSendRecord Model (Backend 引用)

使用 shared 模組的批次發送記錄模型。
"""

import sys
from pathlib import Path

# 添加 shared 模組到路徑
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "shared"))

from shared.models.batch_send_record import BatchSendRecord

# 重新匯出供 Backend 使用
__all__ = ["BatchSendRecord"]
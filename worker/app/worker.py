"""
獨立 Worker 主程式

從 backend/app/workers/sqs_worker.py 重構而來，
使用 shared 模組，與 Backend 完全解耦。
"""

import asyncio
import logging
import signal
import sys
from pathlib import Path
from typing import List

# 添加 shared 模組到路徑
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "shared"))

from shared.config.settings import settings
from shared.utils.sqs_client import SQSClient
from app.handlers.message_handler import MessageHandler

logger = logging.getLogger(__name__)


class WorkerService:
    """獨立 Worker 服務"""
    
    def __init__(self):
        self.sqs_client = SQSClient()
        self.message_handler = MessageHandler()
        self.running = False
        self.queues_to_process = ['send_queue', 'batch_queue']
        self.max_messages_per_poll = 10
        self.tasks: List[asyncio.Task] = []
        
    async def start(self):
        """啟動 Worker"""
        self.running = True
        logger.info("Starting Worker Service...")
        
        # 設定信號處理
        self._setup_signal_handlers()
        
        # 驗證配置
        if not await self._validate_config():
            logger.error("Configuration validation failed. Exiting.")
            return
            
        logger.info(f"Worker will process queues: {self.queues_to_process}")
        
        # 為每個佇列啟動處理任務
        for queue_name in self.queues_to_process:
            task = asyncio.create_task(self._process_queue(queue_name))
            self.tasks.append(task)
        
        # 等待所有任務完成
        try:
            await asyncio.gather(*self.tasks)
        except asyncio.CancelledError:
            logger.info("Worker tasks cancelled")
        
        logger.info("Worker Service stopped")
    
    async def stop(self):
        """停止 Worker"""
        self.running = False
        logger.info("Stopping Worker Service...")
        
        # 取消所有任務
        for task in self.tasks:
            task.cancel()
        
        # 等待任務完成取消
        if self.tasks:
            await asyncio.gather(*self.tasks, return_exceptions=True)
    
    def _setup_signal_handlers(self):
        """設定信號處理器"""
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, initiating graceful shutdown...")
            asyncio.create_task(self.stop())
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    async def _validate_config(self) -> bool:
        """驗證配置"""
        try:
            # 測試 SQS 連接
            if not await self.sqs_client.test_connection():
                logger.error("SQS connection test failed")
                return False
                
            logger.info("Configuration validated successfully")
            return True
            
        except Exception as e:
            logger.error(f"Configuration validation failed: {e}")
            return False
    
    async def _process_queue(self, queue_name: str):
        """處理單一佇列的訊息"""
        logger.info(f"Started processing queue: {queue_name}")
        
        while self.running:
            try:
                # 接收訊息
                messages = await self.sqs_client.receive_messages(
                    queue_name=queue_name,
                    max_messages=self.max_messages_per_poll,
                    wait_time_seconds=20  # 長輪詢
                )
                
                if not messages:
                    continue
                
                # 處理每個訊息
                for message in messages:
                    try:
                        success = await self.message_handler.handle_message(queue_name, message)
                        
                        # 成功處理後刪除訊息
                        if success:
                            await self.sqs_client.delete_message(
                                queue_name, message['receipt_handle']
                            )
                            logger.info(f"Message {message['message_id']} processed and deleted")
                        else:
                            logger.warning(f"Message {message['message_id']} processing failed, will retry")
                            
                    except Exception as e:
                        logger.error(f"Error processing message {message['message_id']}: {e}")
                        # 訊息處理失敗會自動回到佇列，超過重試次數後進入 DLQ
                
            except Exception as e:
                logger.error(f"Error in queue processing loop for {queue_name}: {e}")
                await asyncio.sleep(1)
        
        logger.info(f"Stopped processing queue: {queue_name}")


async def main():
    """Worker 主函數"""
    # 設定日誌
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger.info(f"Starting Worker with project: {settings.project_name}")
    logger.info(f"Database URL: {settings.database.server}")
    logger.info(f"SQS Endpoint: {settings.aws.sqs_endpoint_url}")
    
    # 建立並啟動 Worker
    worker = WorkerService()
    await worker.start()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Worker interrupted by user")
    except Exception as e:
        logger.error(f"Worker failed with error: {e}")
        sys.exit(1)
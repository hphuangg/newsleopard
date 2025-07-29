"""
SQS Worker 系統

替代 Celery，直接處理 SQS 佇列中的發送任務。
"""

import asyncio
import json
import logging
import signal
import sys
from typing import Dict, Any, Optional
from datetime import datetime
from contextlib import asynccontextmanager

from app.services.sqs_queue_manager import sqs_queue_manager
from app.core.config import settings

logger = logging.getLogger(__name__)


class SQSWorker:
    """SQS Worker 核心處理器"""
    
    def __init__(self):
        self.running = False
        self.queues_to_process = ['send_queue', 'batch_queue']
        self.max_messages_per_poll = 10
        self.poll_interval = 1  # 秒
        self.tasks = []
        
    async def start(self):
        """啟動 Worker"""
        self.running = True
        logger.info("Starting SQS Worker...")
        
        # 設定信號處理
        self._setup_signal_handlers()
        
        # 驗證 SQS 配置
        if not await self._validate_configuration():
            logger.error("SQS configuration validation failed. Exiting.")
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
        
        logger.info("SQS Worker stopped")
    
    async def stop(self):
        """停止 Worker"""
        self.running = False
        logger.info("Stopping SQS Worker...")
        
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
    
    async def _validate_configuration(self) -> bool:
        """驗證配置"""
        try:
            # 簡化驗證：嘗試接收訊息來測試連接
            for queue_name in self.queues_to_process:
                try:
                    # 嘗試從佇列接收訊息（不等待，立即返回）
                    await sqs_queue_manager.receive_messages(
                        queue_name=queue_name,
                        max_messages=1,
                        wait_time_seconds=0
                    )
                    logger.info(f"Queue {queue_name} is accessible")
                except Exception as e:
                    logger.error(f"Queue {queue_name} is not accessible: {e}")
                    return False
            
            logger.info("SQS configuration validated successfully")
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
                messages = await sqs_queue_manager.receive_messages(
                    queue_name=queue_name,
                    max_messages=self.max_messages_per_poll,
                    wait_time_seconds=20  # 長輪詢
                )
                
                if not messages:
                    continue
                
                # 處理每個訊息
                for message in messages:
                    try:
                        await self._process_message(queue_name, message)
                    except Exception as e:
                        logger.error(f"Error processing message {message['message_id']}: {e}")
                        # 訊息處理失敗會自動回到佇列，超過重試次數後進入 DLQ
                
            except Exception as e:
                logger.error(f"Error in queue processing loop for {queue_name}: {e}")
                await asyncio.sleep(self.poll_interval)
        
        logger.info(f"Stopped processing queue: {queue_name}")
    
    async def _process_message(self, queue_name: str, message: Dict[str, Any]):
        """處理單一訊息"""
        message_id = message['message_id']
        receipt_handle = message['receipt_handle']
        body = message['body']
        
        logger.info(f"Processing message {message_id} from {queue_name}")
        
        try:
            # 根據佇列類型處理訊息
            if queue_name == 'send_queue':
                result = await self._handle_send_message(body)
            elif queue_name == 'batch_queue':
                result = await self._handle_batch_send(body)
            else:
                logger.error(f"Unknown queue type: {queue_name}")
                return
            
            # 處理成功，刪除訊息
            if result.get('success', False):
                await sqs_queue_manager.delete_message(queue_name, receipt_handle)
                logger.info(f"Message {message_id} processed successfully")
            else:
                logger.error(f"Message {message_id} processing failed: {result.get('error', 'Unknown error')}")
                # 不刪除訊息，讓它回到佇列重試
                
        except Exception as e:
            logger.error(f"Exception processing message {message_id}: {e}")
            # 不刪除訊息，讓它回到佇列重試
    
    async def _handle_send_message(self, message_data: Dict[str, Any]) -> Dict[str, Any]:
        """處理單一訊息發送"""
        try:
            # 提取訊息資料
            batch_id = message_data.get('batch_id')
            message_id = message_data.get('message_id')
            channel = message_data.get('channel')
            content = message_data.get('content')
            recipient = message_data.get('recipient')
            
            logger.info(f"Sending single message: batch_id={batch_id}, message_id={message_id}, channel={channel}")
            
            # TODO: 實際的發送邏輯 (整合 TASK-04 發送管道抽象層)
            # 目前模擬發送
            await asyncio.sleep(0.5)  # 模擬發送延遲
            
            # 模擬發送結果
            success_rate = 0.9  # 90% 成功率
            import random
            is_success = random.random() < success_rate
            
            if is_success:
                # TODO: 更新資料庫記錄為成功
                logger.info(f"Message {message_id} sent successfully")
                return {
                    'success': True,
                    'message_id': message_id,
                    'status': 'sent',
                    'sent_at': datetime.utcnow().isoformat()
                }
            else:
                # TODO: 更新資料庫記錄為失敗
                logger.warning(f"Message {message_id} send failed")
                return {
                    'success': False,
                    'message_id': message_id,
                    'error': 'Simulated send failure'
                }
                
        except Exception as e:
            logger.error(f"Error in _handle_send_message: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _handle_batch_send(self, message_data: Dict[str, Any]) -> Dict[str, Any]:
        """處理批次訊息發送"""
        try:
            batch_id = message_data.get('batch_id')
            channel = message_data.get('channel')
            content = message_data.get('content')
            recipients = message_data.get('recipients', [])
            
            logger.info(f"Sending batch message: batch_id={batch_id}, channel={channel}, recipients={len(recipients)}")
            
            # TODO: 實際的批次發送邏輯
            # 目前模擬批次發送
            results = []
            for recipient in recipients:
                await asyncio.sleep(0.1)  # 模擬每個發送的延遲
                
                # 模擬發送結果
                import random
                is_success = random.random() < 0.85  # 85% 成功率
                
                result = {
                    'recipient_id': recipient.get('id'),
                    'message_id': recipient.get('message_id'),
                    'success': is_success,
                    'status': 'sent' if is_success else 'failed',
                    'error': None if is_success else 'Simulated batch send failure'
                }
                results.append(result)
            
            # 統計結果
            success_count = sum(1 for r in results if r['success'])
            failed_count = len(results) - success_count
            
            logger.info(f"Batch {batch_id} completed: {success_count} success, {failed_count} failed")
            
            # TODO: 更新批次統計
            
            return {
                'success': True,
                'batch_id': batch_id,
                'total_count': len(results),
                'success_count': success_count,
                'failed_count': failed_count,
                'results': results
            }
            
        except Exception as e:
            logger.error(f"Error in _handle_batch_send: {e}")
            return {
                'success': False,
                'error': str(e)
            }


async def main():
    """Worker 主函數"""
    # 設定日誌
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 建立並啟動 Worker
    worker = SQSWorker()
    await worker.start()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Worker interrupted by user")
    except Exception as e:
        logger.error(f"Worker failed with error: {e}")
        sys.exit(1)
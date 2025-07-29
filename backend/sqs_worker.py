#!/usr/bin/env python3
"""
SQS Worker 啟動腳本

用於啟動 SQS Worker 處理發送任務。
"""

import sys
import os
import asyncio
import logging

# 添加專案根目錄到 Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.workers.sqs_worker import SQSWorker

def main():
    """啟動 SQS Worker"""
    print("🚀 Starting SQS Worker for NewsLeopard...")
    print("📋 Worker will process: send_queue, batch_queue")
    print("🔧 Press Ctrl+C to stop gracefully")
    print("-" * 50)
    
    # 設定日誌
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('sqs_worker.log')
        ]
    )
    
    # 建立並啟動 Worker
    worker = SQSWorker()
    
    try:
        asyncio.run(worker.start())
    except KeyboardInterrupt:
        print("\n⏹️  Worker stopped by user")
    except Exception as e:
        print(f"\n❌ Worker failed: {e}")
        logging.error(f"Worker failed with error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
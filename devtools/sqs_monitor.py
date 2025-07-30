#!/usr/bin/env python3
"""
SQS 佇列監控工具

用於查看 LocalStack SQS 佇列的內容和狀態
"""

import os
import sys
import asyncio
import json
from datetime import datetime

# 設置環境變數
os.environ.setdefault('AWS_ACCESS_KEY_ID', 'test')
os.environ.setdefault('AWS_SECRET_ACCESS_KEY', 'test')
os.environ.setdefault('AWS_REGION', 'us-east-1')
os.environ.setdefault('AWS_SQS_ENDPOINT_URL', 'http://localhost:4566')
os.environ.setdefault('SQS_SEND_QUEUE_URL', 'http://sqs.us-east-1.localhost.localstack.cloud:4566/000000000000/send-queue')
os.environ.setdefault('SQS_BATCH_QUEUE_URL', 'http://sqs.us-east-1.localhost.localstack.cloud:4566/000000000000/batch-queue')
os.environ.setdefault('SQS_SEND_DLQ_URL', 'http://sqs.us-east-1.localhost.localstack.cloud:4566/000000000000/send-dlq')
os.environ.setdefault('SQS_BATCH_DLQ_URL', 'http://sqs.us-east-1.localhost.localstack.cloud:4566/000000000000/batch-dlq')

# 添加專案路徑
current_dir = os.path.dirname(os.path.abspath(__file__))  # devtools 目錄
project_root = os.path.dirname(current_dir)  # 專案根目錄
sys.path.insert(0, os.path.join(project_root, 'backend'))  # backend 目錄
sys.path.insert(0, project_root)  # 專案根目錄，讓 shared 可以被找到

from app.services.sqs_queue_manager import sqs_queue_manager

async def show_queue_status():
    """顯示所有佇列狀態"""
    print("🔍 SQS 佇列監控")
    print("=" * 60)
    print(f"⏰ 時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    queues = ['send_queue', 'batch_queue', 'send_dlq', 'batch_dlq']
    
    for queue_name in queues:
        print(f"📦 {queue_name.upper()}:")
        
        try:
            # 接收訊息但不刪除（peek 模式）
            messages = await sqs_queue_manager.receive_messages(
                queue_name=queue_name,
                max_messages=10,
                wait_time_seconds=1  # 短暫等待
            )
            
            if messages:
                print(f"   📊 訊息數量: {len(messages)}")
                print("   📄 訊息內容:")
                
                for i, msg in enumerate(messages, 1):
                    body = msg['body']
                    print(f"      [{i}] Message ID: {msg['message_id'][:8]}...")
                    print(f"          Type: {body.get('type', 'unknown')}")
                    print(f"          Batch ID: {body.get('batch_id', 'N/A')[:8]}...")
                    if 'content' in body:
                        content = body['content'][:50] + '...' if len(body['content']) > 50 else body['content']
                        print(f"          Content: {content}")
                    if 'recipients' in body:
                        print(f"          Recipients: {len(body['recipients'])} 個")
                    print()
                
                # 把訊息放回佇列（不刪除）
                print(f"   💡 注意: 檢視後訊息仍在佇列中")
            else:
                print("   📊 訊息數量: 0 (佇列為空)")
            
        except Exception as e:
            print(f"   ❌ 錯誤: {str(e)}")
        
        print("-" * 40)

async def peek_messages():
    """查看訊息但不刪除"""
    await show_queue_status()

async def consume_messages():
    """消費訊息（會從佇列中刪除）"""
    queues = ['send_queue', 'batch_queue']
    
    print("🔄 開始消費訊息...")
    print("=" * 60)
    
    for queue_name in queues:
        print(f"\n📦 處理 {queue_name.upper()}:")
        
        while True:
            try:
                # 接收訊息
                messages = await sqs_queue_manager.receive_messages(
                    queue_name=queue_name,
                    max_messages=1,
                    wait_time_seconds=2
                )
                
                if not messages:
                    print(f"   ✅ {queue_name} 已處理完畢")
                    break
                
                msg = messages[0]
                body = msg['body']
                
                print(f"   📄 處理訊息: {msg['message_id'][:8]}...")
                print(f"       Type: {body.get('type', 'unknown')}")
                print(f"       Batch ID: {body.get('batch_id', 'N/A')[:8]}...")
                
                # 模擬處理
                await asyncio.sleep(0.1)
                
                # 刪除訊息
                deleted = await sqs_queue_manager.delete_message(
                    queue_name=queue_name,
                    receipt_handle=msg['receipt_handle']
                )
                
                if deleted:
                    print(f"       ✅ 訊息已處理並刪除")
                else:
                    print(f"       ❌ 訊息刪除失敗")
                
            except Exception as e:
                print(f"   ❌ 處理錯誤: {str(e)}")
                break

async def continuous_monitor():
    """持續監控佇列狀態"""
    print("🔄 開始持續監控 SQS 佇列...")
    print("按 Ctrl+C 停止監控")
    print("=" * 60)
    
    try:
        while True:
            # 清屏
            os.system('clear' if os.name == 'posix' else 'cls')
            
            # 顯示當前時間
            print(f"⏰ 監控時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print("=" * 60)
            
            # 顯示佇列狀態
            await show_queue_status()
            
            # 等待3秒
            await asyncio.sleep(3)
            
    except KeyboardInterrupt:
        print("\n⏹️  監控已停止")
    except Exception as e:
        print(f"\n❌ 監控錯誤: {e}")

def show_help():
    """顯示使用說明"""
    print("🚀 SQS 佇列監控工具")
    print("=" * 60)
    print("使用方式:")
    print("  python sqs_monitor.py [command]")
    print()
    print("可用命令:")
    print("  status    - 查看佇列狀態和訊息內容（不刪除訊息）")
    print("  peek      - 同 status")
    print("  consume   - 處理並刪除佇列中的訊息")
    print("  monitor   - 持續監控佇列狀態（每3秒更新）")
    print("  help      - 顯示此說明")
    print()
    print("範例:")
    print("  python sqs_monitor.py status     # 查看佇列狀態")
    print("  python sqs_monitor.py consume    # 處理所有訊息")
    print("  python sqs_monitor.py monitor    # 持續監控")

async def main():
    """主函數"""
    command = sys.argv[1] if len(sys.argv) > 1 else 'status'
    
    if command in ['status', 'peek']:
        await peek_messages()
    elif command == 'consume':
        await consume_messages()
    elif command == 'monitor':
        await continuous_monitor()
    elif command == 'help':
        show_help()
    else:
        print(f"❌ 未知命令: {command}")
        show_help()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⏹️  監控已停止")
    except Exception as e:
        print(f"\n❌ 錯誤: {e}")
        import traceback
        traceback.print_exc()
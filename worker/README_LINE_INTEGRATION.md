# Line Bot 整合測試指南

這個文件說明如何測試 NewsLeopard Worker 與 Line Bot 的整合功能。

## 前置準備

### 1. Line Bot 設定

1. 前往 [Line Developers Console](https://developers.line.biz/)
2. 建立新的 Line Bot 或選擇現有的
3. 取得以下資訊：
   - Channel Access Token
   - Channel Secret (可選)

### 2. 環境變數設定

複製並編輯環境變數檔案：

```bash
# 從專案根目錄
cp .env.example .env
```

編輯 `.env` 檔案，填入真實的 Line Bot 資訊：

```bash
# Line Bot 配置
LINE_CHANNEL_ACCESS_TOKEN=YOUR_REAL_CHANNEL_ACCESS_TOKEN
LINE_CHANNEL_SECRET=YOUR_REAL_CHANNEL_SECRET
```

### 3. 安裝依賴

```bash
# 在 worker 目錄下
cd worker
pip install -r requirements.txt
```

## 測試方法

### 方法 1: 直接測試 Line Bot 功能

這個測試不依賴 SQS，直接測試 Line Bot 發送功能：

```bash
cd worker
python test_line_push.py
```

**注意**: 這個測試使用假的收件人 ID，如果沒有設定真實的 Line Bot Token，會在驗證階段通過但發送階段失敗。

### 方法 2: 完整 SQS + Line Bot 流程測試

這個測試會發送訊息到 SQS 佇列，然後您需要啟動 Worker 來處理：

#### 步驟 1: 啟動必要服務

```bash
# 啟動 LocalStack (SQS)
docker-compose up localstack -d

# 啟動資料庫 (如果需要)
docker-compose up postgres -d
```

#### 步驟 2: 發送測試訊息到 SQS

```bash
cd worker
python test_sqs_line_flow.py
```

#### 步驟 3: 啟動 Worker 處理訊息

```bash
cd worker
python -m app.worker
```

## 測試腳本說明

### test_line_push.py

- **功能**: 直接測試 Line Bot 管道
- **測試項目**:
  - Line Bot 管道初始化
  - 收件人 ID 格式驗證
  - 訊息發送功能 (使用測試 ID)

### test_sqs_line_flow.py

- **功能**: 測試完整的 SQS → Worker → Line Bot 流程
- **測試項目**:
  - SQS 連接測試
  - 發送單一訊息到 send_queue
  - 發送批次訊息到 batch_queue
  - 提供 Worker 啟動指示

## 真實 Line Bot 測試

要進行真實的 Line Bot 測試，您需要：

1. **取得真實的 Line 用戶 ID**:
   - 讓用戶加您的 Line Bot 為好友
   - 從 webhook 事件中取得用戶 ID
   - 或使用 Line Bot 的其他 API 取得

2. **修改測試腳本中的收件人 ID**:
   ```python
   # 在 test_line_push.py 中
   test_recipient = "U你的真實用戶ID"
   
   # 在 test_sqs_line_flow.py 中
   "recipient": "U你的真實用戶ID"
   ```

3. **執行測試**:
   ```bash
   python test_line_push.py
   ```

## 預期的測試結果

### 成功的 Line Bot 測試

```
🚀 Starting Line Bot push test...
📱 Initializing Line Bot channel...
INFO - LineBotChannel initialized with rate limit: 1000/3600s
📋 Line Bot channel available: True
📤 Sending test message to U1234567890abcdef1234567890abcdef12
✅ Test message sent successfully!
📊 Message ID: some-line-response-id
🎉 All tests passed!
```

### Line Bot 配置錯誤

```
❌ Line Bot channel is not available. Please check configuration.
🔧 Configuration error: Line Bot Channel Access Token is required
💡 請檢查環境變數:
   - LINE_CHANNEL_ACCESS_TOKEN: Line Bot Channel Access Token
```

### SQS 流程測試成功

```
✅ Message sent to SQS successfully!
🔍 Message details:
   - Message ID: 12345678-1234-1234-1234-123456789012
   - Channel: line
   - Recipient: U1234567890abcdef1234567890abcdef12
🔔 Now start the worker to process this message:
   cd worker && python -m app.worker
```

## 故障排除

### 常見問題

1. **Line Bot Token 無效**:
   - 檢查 `.env` 檔案中的 `LINE_CHANNEL_ACCESS_TOKEN`
   - 確認 Token 沒有過期
   - 確認 Token 有發送訊息的權限

2. **SQS 連接失敗**:
   - 確認 LocalStack 正在運行: `docker ps | grep localstack`
   - 檢查 SQS 端點 URL 設定

3. **收件人 ID 格式錯誤**:
   - Line 用戶 ID 格式: `U` + 32 字元英數字
   - 確認使用真實的用戶 ID

4. **Worker 無法處理訊息**:
   - 檢查 Worker 日誌輸出
   - 確認所有依賴都已正確安裝
   - 檢查環境變數設定

### 日誌級別調整

如需更詳細的除錯訊息，可以修改日誌級別：

```python
# 在測試腳本中
logging.basicConfig(level=logging.DEBUG)
```

## 後續開發

這個實作提供了基本的 Line Bot 整合功能。後續可以擴展：

1. **多管道支援**: 新增 SMS、Email 等其他發送管道
2. **錯誤重試機制**: 實作訊息發送失敗的重試邏輯
3. **發送狀態追蹤**: 將發送結果寫入資料庫
4. **頻率限制優化**: 使用 Redis 實作分散式頻率限制
5. **批次發送優化**: 實作真實的批次發送邏輯
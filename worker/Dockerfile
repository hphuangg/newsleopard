FROM python:3.11-slim

WORKDIR /app

# 安裝 Worker 依賴
COPY worker/requirements.txt ./worker/requirements.txt
RUN pip install -r worker/requirements.txt

# 複製共用模組和 Worker 代碼
COPY shared/ ./shared/
COPY worker/ ./worker/

# 設定 Python 路徑
ENV PYTHONPATH=/app

# 建立非 root 使用者
RUN groupadd -r worker && useradd -r -g worker worker
RUN chown -R worker:worker /app
USER worker

CMD ["python", "worker/app/worker.py"]
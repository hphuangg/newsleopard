FROM python:3.11-slim

WORKDIR /app

# 安裝 Backend 依賴
COPY backend/requirements.txt ./backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

# 複製共用模組和 Backend 代碼
COPY shared/ ./shared/
COPY backend/ ./backend/

# 設定 Python 路徑
ENV PYTHONPATH=/app

# 建立非 root 使用者
RUN groupadd -r backend && useradd -r -g backend backend
RUN chown -R backend:backend /app
USER backend

EXPOSE 8000

CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
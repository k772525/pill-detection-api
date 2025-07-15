FROM python:3.10-slim

WORKDIR /app

# 安裝 OpenCV/YOLO 依賴和字型相關工具
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    fontconfig \
    fonts-noto-cjk \
    wget \
    && rm -rf /var/lib/apt/lists/*

# 預先升級 pip setuptools wheel，避免 numpy/torch 等新版 whl 抓不到
RUN python -m pip install --upgrade pip setuptools wheel

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 從GitHub Release下載模型文件 (在 COPY . . 之前)
RUN mkdir -p models && \
    echo "正在下載模型文件..." && \
    curl -L -f --connect-timeout 30 --max-time 300 --retry 3 --retry-delay 5 \
         -o models/YOLOv12.pt \
         "https://github.com/k772525/pill-detection-api/releases/download/v1.0.0/YOLOv12.pt" && \
    echo "模型下載成功，文件大小：$(du -h models/YOLOv12.pt)" && \
    ls -la models/ || \
    (echo "模型下載失敗，嘗試其他版本..." && \
     curl -L -f --connect-timeout 30 --max-time 300 --retry 3 --retry-delay 5 \
          -o models/YOLOv12.pt \
          "https://github.com/k772525/pill-detection-api/releases/download/v1.0.1/YOLOv12.pt" && \
     echo "模型下載成功 (v1.0.1)，文件大小：$(du -h models/YOLOv12.pt)" || \
     (echo "所有版本的模型下載都失敗了" && exit 1))

# 複製應用程式代碼 (不包括本地 models/)
COPY . .

# 驗證模型文件存在
RUN ls -la models/ && \
    if [ -f models/YOLOv12.pt ]; then \
        echo "✅ 模型文件存在，大小：$(du -h models/YOLOv12.pt)"; \
    else \
        echo "❌ 模型文件不存在！"; \
        exit 1; \
    fi

# 安裝中文字型 (使用 Python 腳本)
RUN python setup_fonts_gcp.py install

ENV GOOGLE_APPLICATION_CREDENTIALS="/app/cji25.json"
ENV PORT=8080
ENV PYTHONPATH="/app"

EXPOSE 8080
CMD exec uvicorn fastapi_app:app --host 0.0.0.0 --port $PORT --workers 1
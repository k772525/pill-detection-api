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

COPY . .

# 從GitHub Release下載模型文件
RUN mkdir -p models && \
    curl -L -o models/YOLOv12.pt \
    "https://github.com/k772525/pill-detection-api/releases/download/v1.0.0/YOLOv12.pt" || \
    echo "模型下載失敗，請檢查Release中是否有YOLOv12.pt文件"

# 安裝中文字型 (使用 Python 腳本)
RUN python setup_fonts_gcp.py install

ENV GOOGLE_APPLICATION_CREDENTIALS="/app/cji25.json"
ENV PORT=8080
ENV PYTHONPATH="/app"

EXPOSE 8080
CMD exec uvicorn fastapi_app:app --host 0.0.0.0 --port $PORT --workers 1
# 藥丸檢測API (Pill Detection API)

基於YOLO模型的藥丸檢測FastAPI應用，支援圖片上傳和藥丸識別功能。

## 功能特點

- 🔍 基於YOLOv12模型的藥丸檢測
- 📸 支援圖片上傳和即時檢測
- 🌐 RESTful API介面
- ☁️ 支援Google Cloud Run部署
- 🗄️ 整合Cloud SQL資料庫
- 🎨 中文字型支援

## 技術堆疊

- **後端框架**: FastAPI
- **機器學習**: YOLOv12, Ultralytics
- **圖像處理**: OpenCV, Pillow
- **資料庫**: MySQL (Cloud SQL)
- **雲端服務**: Google Cloud Run, Google Cloud Storage
- **容器化**: Docker

## 快速開始

### 環境需求

- Python 3.10+
- Docker (可選)
- Google Cloud SDK (部署時需要)

### 本地執行

1. 複製儲存庫
```bash
git clone https://github.com/YOUR_USERNAME/pill-detection-api.git
cd pill-detection-api
```

2. 下載模型檔案
從 [Releases](https://github.com/YOUR_USERNAME/pill-detection-api/releases) 頁面下載最新的模型檔案，並放置在 `models/` 目錄下。

3. 安裝相依套件
```bash
pip install -r requirements.txt
```

4. 設定環境變數
建立 `env.yaml` 檔案並設定資料庫連線資訊：
```yaml
GCS_BUCKET_NAME: "your-bucket-name"
DB_HOST: 'your-db-host'
DB_USER: 'your-db-user'
DB_PASS: 'your-db-password'
DB_NAME: 'your-db-name'
```

5. 啟動應用程式
```bash
uvicorn fastapi_app:app --host 0.0.0.0 --port 8080
```

### Docker執行

```bash
docker build -t pill-detection-api .
docker run -p 8080:8080 pill-detection-api
```

## API文件

啟動應用程式後，造訪以下網址查看API文件：
- Swagger UI: `http://localhost:8080/docs`
- ReDoc: `http://localhost:8080/redoc`

### 主要介面

- `POST /detect_pills` - 藥丸檢測
- `GET /health` - 健康檢查
- `GET /` - 根路徑

## 部署到Google Cloud Run

### 前置條件

1. 安裝Google Cloud SDK
2. 設定認證: `gcloud auth login`
3. 設定專案: `gcloud config set project YOUR_PROJECT_ID`

### 自動部署 (建議)

本專案設定了GitHub Actions自動部署，當推送到main分支時會自動部署到Cloud Run。

需要在GitHub儲存庫設定中設定以下Secrets：
- `GCP_PROJECT_ID`: Google Cloud專案ID
- `GCP_SA_KEY`: 服務帳號金鑰(JSON格式)

### 手動部署

```bash
# 建置並推送到Artifact Registry
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/pill-detection-api

# 部署到Cloud Run
gcloud run deploy pill-detection-api \
  --image gcr.io/YOUR_PROJECT_ID/pill-detection-api \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

## 專案結構

```
├── fastapi_app.py          # 主應用程式檔案
├── modules/
│   └── yolo_pill_analyzer.py  # YOLO分析模組
├── models/                 # 模型檔案 (從Releases下載)
│   └── YOLOv12.pt
├── requirements.txt        # Python相依套件
├── Dockerfile             # Docker設定
├── .dockerignore          # Docker忽略檔案
├── env.yaml              # 環境設定
├── setup_fonts_gcp.py    # 字型安裝腳本
└── db_cloud_sql.py       # 資料庫連線
```

## 開發指南

### 新增功能

1. 在 `modules/` 目錄下新增模組
2. 在 `fastapi_app.py` 中新增API端點
3. 如有新的相依套件，請更新 `requirements.txt`
4. 新增對應的測試

### 模型更新

1. 將新模型檔案放在 `models/` 目錄
2. 更新 `modules/yolo_pill_analyzer.py` 中的模型路徑
3. 建立新的Release並上傳模型檔案

## 貢獻

歡迎提交Issue和Pull Request！

## 授權條款

MIT License

## 聯絡方式

如有問題，請提交Issue或聯絡維護者。
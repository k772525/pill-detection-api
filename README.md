# 药丸检测API (Pill Detection API)

基于YOLO模型的药丸检测FastAPI应用，支持图片上传和药丸识别功能。

## 功能特点

- 🔍 基于YOLOv12模型的药丸检测
- 📸 支持图片上传和实时检测
- 🌐 RESTful API接口
- ☁️ 支持Google Cloud Run部署
- 🗄️ 集成Cloud SQL数据库
- 🎨 中文字体支持

## 技术栈

- **后端框架**: FastAPI
- **机器学习**: YOLOv12, Ultralytics
- **图像处理**: OpenCV, Pillow
- **数据库**: MySQL (Cloud SQL)
- **云服务**: Google Cloud Run, Google Cloud Storage
- **容器化**: Docker

## 快速开始

### 环境要求

- Python 3.10+
- Docker (可选)
- Google Cloud SDK (部署时需要)

### 本地运行

1. 克隆仓库
```bash
git clone https://github.com/YOUR_USERNAME/pill-detection-api.git
cd pill-detection-api
```

2. 下载模型文件
从 [Releases](https://github.com/YOUR_USERNAME/pill-detection-api/releases) 页面下载最新的模型文件，并放置在 `models/` 目录下。

3. 安装依赖
```bash
pip install -r requirements.txt
```

4. 配置环境变量
创建 `env.yaml` 文件并配置数据库连接信息：
```yaml
GCS_BUCKET_NAME: "your-bucket-name"
DB_HOST: 'your-db-host'
DB_USER: 'your-db-user'
DB_PASS: 'your-db-password'
DB_NAME: 'your-db-name'
```

5. 启动应用
```bash
uvicorn fastapi_app:app --host 0.0.0.0 --port 8080
```

### Docker运行

```bash
docker build -t pill-detection-api .
docker run -p 8080:8080 pill-detection-api
```

## API文档

启动应用后，访问以下地址查看API文档：
- Swagger UI: `http://localhost:8080/docs`
- ReDoc: `http://localhost:8080/redoc`

### 主要接口

- `POST /detect_pills` - 药丸检测
- `GET /health` - 健康检查
- `GET /` - 根路径

## 部署到Google Cloud Run

### 前置条件

1. 安装Google Cloud SDK
2. 配置认证: `gcloud auth login`
3. 设置项目: `gcloud config set project YOUR_PROJECT_ID`

### 自动部署 (推荐)

本项目配置了GitHub Actions自动部署，当推送到main分支时会自动部署到Cloud Run。

需要在GitHub仓库设置中配置以下Secrets：
- `GCP_PROJECT_ID`: Google Cloud项目ID
- `GCP_SA_KEY`: 服务账号密钥(JSON格式)

### 手动部署

```bash
# 构建并推送到Artifact Registry
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/pill-detection-api

# 部署到Cloud Run
gcloud run deploy pill-detection-api \
  --image gcr.io/YOUR_PROJECT_ID/pill-detection-api \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

## 项目结构

```
├── fastapi_app.py          # 主应用文件
├── modules/
│   └── yolo_pill_analyzer.py  # YOLO分析模块
├── models/                 # 模型文件 (从Releases下载)
│   └── YOLOv12.pt
├── requirements.txt        # Python依赖
├── Dockerfile             # Docker配置
├── .dockerignore          # Docker忽略文件
├── env.yaml              # 环境配置
├── setup_fonts_gcp.py    # 字体安装脚本
└── db_cloud_sql.py       # 数据库连接
```

## 开发指南

### 添加新功能

1. 在 `modules/` 目录下添加新模块
2. 在 `fastapi_app.py` 中添加新的API端点
3. 更新 `requirements.txt` 如果有新依赖
4. 添加相应的测试

### 模型更新

1. 将新模型文件放在 `models/` 目录
2. 更新 `modules/yolo_pill_analyzer.py` 中的模型路径
3. 创建新的Release并上传模型文件

## 贡献

欢迎提交Issue和Pull Request！

## 许可证

MIT License

## 联系方式

如有问题，请提交Issue或联系维护者。
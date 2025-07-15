# 上传模型文件到GitHub Releases

由于模型文件较大(53MB)，我们将其存储在GitHub Releases中而不是直接提交到仓库。

## 步骤1: 创建Release

1. 进入您的GitHub仓库页面
2. 点击右侧的 "Releases"
3. 点击 "Create a new release"

## 步骤2: 配置Release

### 标签信息
- **Tag version**: `v1.0.0`
- **Target**: `main` (默认)

### Release标题
```
Release v1.0.0 - 初始版本
```

### Release描述
```markdown
## 药丸检测API v1.0.0

### 🎉 首次发布

这是药丸检测API的首个正式版本，包含完整的YOLO模型和FastAPI服务。

### 📦 包含内容

- **YOLOv12.pt** - 药丸检测模型 (53MB)
  - 基于YOLOv12架构
  - 支持多种药丸类型检测
  - 优化的推理性能

### 🚀 快速开始

1. 下载模型文件 `YOLOv12.pt`
2. 将文件放置在项目的 `models/` 目录下
3. 运行应用: `uvicorn fastapi_app:app --host 0.0.0.0 --port 8080`

### 📋 系统要求

- Python 3.10+
- 内存: 至少2GB
- 存储: 至少1GB可用空间
- GPU: 可选，用于加速推理

### 🔧 部署支持

- ✅ Google Cloud Run
- ✅ Docker容器
- ✅ 本地开发环境

### 📚 文档

- [API文档](http://localhost:8080/docs)
- [部署指南](README.md#部署到google-cloud-run)
- [贡献指南](CONTRIBUTING.md)

### 🐛 已知问题

- 首次加载模型可能需要较长时间
- 大图片处理可能超时（建议压缩到1MB以下）

### 📞 支持

如有问题，请提交 [Issue](https://github.com/YOUR_USERNAME/pill-detection-api/issues)
```

## 步骤3: 上传模型文件

1. 在Release编辑页面底部找到 "Attach binaries by dropping them here or selecting them"
2. 点击选择文件或直接拖拽 `models/YOLOv12.pt` 文件
3. 等待文件上传完成（可能需要几分钟）

## 步骤4: 发布Release

1. 确认所有信息正确
2. 点击 "Publish release"

## 步骤5: 验证

发布后，您可以：

1. 在Releases页面看到新的v1.0.0版本
2. 点击模型文件名可以下载
3. 复制下载链接用于自动化脚本

## 自动下载脚本

创建一个脚本来自动下载模型：

```bash
#!/bin/bash
# download_model.sh

GITHUB_USER="YOUR_USERNAME"
REPO_NAME="pill-detection-api"
MODEL_FILE="YOLOv12.pt"
VERSION="v1.0.0"

echo "下载模型文件..."
mkdir -p models
cd models

# 下载模型文件
curl -L -o $MODEL_FILE \
  "https://github.com/$GITHUB_USER/$REPO_NAME/releases/download/$VERSION/$MODEL_FILE"

echo "模型文件下载完成: models/$MODEL_FILE"
```

## 注意事项

- 模型文件会计入您的GitHub存储配额
- 公开仓库的Release文件可以被任何人下载
- 建议在Release描述中包含模型的详细信息
- 可以为不同版本的模型创建不同的Release标签

## 更新模型

当需要更新模型时：

1. 创建新的Release（如v1.1.0）
2. 上传新的模型文件
3. 在Release描述中说明更新内容
4. 更新应用代码中的模型版本引用
# 🚀 手动创建GitHub Release指南

由于GitHub Actions权限限制，建议手动创建Release来上传模型文件。

## 📋 步骤1: 推送标签

在本地项目目录中运行：

```bash
# 创建并推送标签
git tag v1.0.0
git push origin v1.0.0
```

## 📦 步骤2: 创建Release

1. **进入GitHub仓库页面**
2. **点击右侧的 "Releases"**
3. **点击 "Create a new release"**

## ⚙️ 步骤3: 配置Release

### 基本信息
- **Choose a tag**: 选择 `v1.0.0` (刚才推送的标签)
- **Release title**: `Release v1.0.0 - 药丸检测API初始版本`

### Release描述
复制以下内容到描述框：

```markdown
## 🎉 药丸检测API v1.0.0 - 初始版本

### 📦 包含内容

- **YOLOv12.pt** - 药丸检测模型 (~53MB)
  - 基于YOLOv12架构训练
  - 支持多种药丸类型检测
  - 优化的推理性能

### 🚀 快速开始

1. **克隆仓库**
   ```bash
   git clone https://github.com/YOUR_USERNAME/pill-detection-api.git
   cd pill-detection-api
   ```

2. **下载模型文件**
   - 从本Release下载 `YOLOv12.pt`
   - 放置到项目的 `models/` 目录下

3. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

4. **启动应用**
   ```bash
   uvicorn fastapi_app:app --host 0.0.0.0 --port 8080
   ```

5. **访问API文档**
   - 打开浏览器访问: http://localhost:8080/docs

### 📋 系统要求

- **Python**: 3.10+
- **内存**: 至少2GB RAM
- **存储**: 至少1GB可用空间
- **GPU**: 可选，用于加速推理

### 🔧 部署选项

- ✅ **Google Cloud Run** - 生产环境推荐
- ✅ **Docker容器** - 容器化部署
- ✅ **本地环境** - 开发和测试

### 🌐 部署到Cloud Run

```bash
# 使用提供的部署脚本
chmod +x deploy.sh
./deploy.sh YOUR_PROJECT_ID us-central1
```

或使用GitHub Actions自动部署（需要配置Secrets）

### 📚 文档链接

- [📖 完整文档](README.md)
- [🤝 贡献指南](CONTRIBUTING.md)
- [🐳 Docker指南](docker-compose.yml)
- [⚙️ 部署脚本](deploy.sh)

### 🔍 API端点

- `POST /detect_pills` - 药丸检测
- `GET /health` - 健康检查
- `GET /docs` - API文档
- `GET /redoc` - ReDoc文档

### 🐛 已知问题

- 首次加载模型可能需要10-30秒
- 大图片(>5MB)处理可能超时，建议压缩到1MB以下
- 中文字体在某些环境下可能需要手动安装

### 📞 获取帮助

- 🐛 [报告Bug](https://github.com/YOUR_USERNAME/pill-detection-api/issues)
- 💡 [功能请求](https://github.com/YOUR_USERNAME/pill-detection-api/issues)
- 📧 技术支持: 通过Issues联系

### 🔄 更新日志

#### v1.0.0 (2024-12-19)
- 🎉 首次发布
- ✨ 基于YOLOv12的药丸检测功能
- 🚀 FastAPI REST API接口
- 🐳 Docker容器化支持
- ☁️ Google Cloud Run部署配置
- 🔄 GitHub Actions CI/CD流程
- 📚 完整的项目文档

---

**⭐ 如果这个项目对您有帮助，请给个Star支持一下！**
```

## 📎 步骤4: 上传模型文件

1. **在Release编辑页面底部找到文件上传区域**
2. **拖拽或点击选择 `models/YOLOv12.pt` 文件**
3. **等待上传完成**（可能需要几分钟，文件约53MB）

## ✅ 步骤5: 发布Release

1. **检查所有信息是否正确**
2. **确保模型文件已上传**
3. **点击 "Publish release"**

## 🎯 验证Release

发布后您可以：

1. **查看Release页面** - 确认信息显示正确
2. **测试下载链接** - 点击模型文件名测试下载
3. **复制下载URL** - 用于自动化脚本

## 🔗 获取下载链接

Release发布后，模型文件的下载链接格式为：
```
https://github.com/YOUR_USERNAME/pill-detection-api/releases/download/v1.0.0/YOLOv12.pt
```

## 📝 后续版本

创建新版本时：
1. 更新代码
2. 创建新标签: `git tag v1.1.0 && git push origin v1.1.0`
3. 重复上述步骤，使用新的版本号

---

**💡 提示**: 手动创建Release虽然需要几个步骤，但可以确保完全控制发布过程，避免权限问题。
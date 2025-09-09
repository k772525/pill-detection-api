# 🔐 GitHub Secrets 設定指南

## 必要的 GitHub Secrets

請在您的 GitHub Repository 中設定以下 Secrets：

### 📍 位置
`Settings` → `Secrets and variables` → `Actions` → `New repository secret`

### 🗄️ 資料庫相關 Secrets

```
名稱: DB_USER
值: your_database_username
描述: Cloud SQL 資料庫用戶名

名稱: DB_PASS  
值: your_database_password
描述: Cloud SQL 資料庫密碼

名稱: DB_NAME
值: pill_detection_db
描述: 資料庫名稱

名稱: CLOUD_SQL_CONNECTION_NAME
值: your-project-id:us-central1:your-instance-name
描述: Cloud SQL 連線名稱
範例: runson-471605:us-central1:pill-detection-db
```

### ☁️ Google Cloud 相關 Secrets

```
名稱: GCP_PROJECT_ID
值: your-gcp-project-id
描述: Google Cloud 專案 ID

名稱: GCP_SA_KEY
值: {"type": "service_account", "project_id": "...", ...}
描述: Google Cloud 服務帳號 JSON 金鑰

名稱: GCS_BUCKET_NAME (可選)
值: your-storage-bucket-name
描述: Google Cloud Storage 儲存桶名稱
```

## 🔍 如何獲取這些值

### 1. Cloud SQL 連線名稱
```bash
gcloud sql instances describe your-instance-name \
    --format="value(connectionName)"
```

### 2. GCP 專案 ID
```bash
gcloud config get-value project
```

### 3. 服務帳號金鑰
```bash
# 創建服務帳號
gcloud iam service-accounts create github-actions \
    --display-name="GitHub Actions"

# 下載金鑰檔案
gcloud iam service-accounts keys create key.json \
    --iam-account=github-actions@your-project-id.iam.gserviceaccount.com

# 將 key.json 的內容複製到 GCP_SA_KEY
```

## ✅ 驗證設定

設定完成後，推送代碼到 main 分支，GitHub Actions 會自動：

1. 🔨 建立 Docker 映像
2. 📤 推送到 Artifact Registry  
3. 🚀 部署到 Cloud Run
4. 🔗 自動設定所有環境變數

## 🔧 故障排除

如果部署失敗，檢查：

1. **Secrets 是否正確設定**
   - 檢查名稱拼寫
   - 確認值沒有多餘空格

2. **Cloud SQL 權限**
   ```bash
   # 為服務帳號添加 Cloud SQL 權限
   gcloud projects add-iam-policy-binding your-project-id \
       --member="serviceAccount:github-actions@your-project-id.iam.gserviceaccount.com" \
       --role="roles/cloudsql.client"
   ```

3. **查看部署日誌**
   - GitHub Actions 頁面查看詳細錯誤
   - Cloud Run 控制台查看服務日誌

## 🎯 完成後的效果

設定完成後，您的 API 將能夠：
- ✅ 自動連接到 Cloud SQL 資料庫
- ✅ 使用正確的資料庫憑證
- ✅ 在 Cloud Run 上穩定運行
- ✅ 支援健康檢查和 API 文檔
# GCP 部署

### 1️⃣ 啟用 API（直接一行執行）

```
gcloud services enable run.googleapis.com artifactregistry.googleapis.com
```

---

### 2️⃣ 建立 Artifact Registry

```
gcloud artifacts repositories create art0718 --repository-format=docker --location=us-central1
```

> ⚠️ 如果你已經建立過，可以略過此步驟。會出現 ALREADY_EXISTS 也沒關係。
> 

---

### 3️⃣ 設定 Docker 認證

```
gcloud auth configure-docker us-central1-docker.pkg.dev
```

---

### 4️⃣ 建立 Docker Image 並推送

```
set PROJECT_ID=gcp-course-20250612
docker build -t us-central1-docker.pkg.dev/gcp-course-20250612/art0718/fastapi:latest .
docker push us-central1-docker.pkg.dev/gcp-course-20250612/art0718/fastapi:latest
```

gcloud run deploy fastapi --image=us-central1-docker.pkg.dev/gcp-course-20250612/art0718/fastapi:latest --region=us-central1 --platform=managed --allow-unauthenticated --memory=4Gi

```





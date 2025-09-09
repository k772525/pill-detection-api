# GCP 部署

### 1️⃣ 啟用 API（直接一行執行）

```
gcloud services enable run.googleapis.com artifactregistry.googleapis.com
```

---

### 2️⃣ 建立 Artifact Registry

```
gcloud artifacts repositories create artrunson --repository-format=docker --location=us-central1
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
set PROJECT_ID=runson-471605
docker build -t us-central1-docker.pkg.dev/runson-471605/artrunson/yolo12:latest .
docker push us-central1-docker.pkg.dev/runson-471605/artrunson/yolo12:latest
```

gcloud run deploy yolo12 --image=us-central1-docker.pkg.dev/runson-471605/artrunson/yolo12:latest --region=us-central1 --platform=managed --allow-unauthenticated --memory=1Gi

```





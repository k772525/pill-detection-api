#!/bin/bash

# 部署測試腳本
# 使用方法: ./test_deployment.sh [SERVICE_URL]

set -e

# 獲取服務URL
if [ -z "$1" ]; then
    echo "🔍 自動獲取服務URL..."
    SERVICE_URL=$(gcloud run services describe pill-detection-api \
        --platform managed \
        --region us-central1 \
        --format 'value(status.url)' 2>/dev/null || echo "")
    
    if [ -z "$SERVICE_URL" ]; then
        echo "❌ 無法獲取服務URL，請手動提供"
        echo "使用方法: $0 https://your-service-url.run.app"
        exit 1
    fi
else
    SERVICE_URL=$1
fi

echo "🧪 測試藥丸檢測API部署"
echo "🌐 服務URL: $SERVICE_URL"
echo ""

# 測試健康檢查
echo "1️⃣ 測試健康檢查..."
if curl -f -s "$SERVICE_URL/health" > /dev/null; then
    echo "✅ 健康檢查通過"
    curl -s "$SERVICE_URL/health" | head -3
else
    echo "❌ 健康檢查失敗"
    exit 1
fi

echo ""

# 測試根路徑
echo "2️⃣ 測試根路徑..."
if curl -f -s "$SERVICE_URL/" > /dev/null; then
    echo "✅ 根路徑訪問正常"
else
    echo "❌ 根路徑訪問失敗"
fi

echo ""

# 測試API文檔
echo "3️⃣ 測試API文檔..."
if curl -f -s "$SERVICE_URL/docs" > /dev/null; then
    echo "✅ API文檔可訪問"
    echo "📚 Swagger UI: $SERVICE_URL/docs"
else
    echo "❌ API文檔訪問失敗"
fi

echo ""

# 測試ReDoc
echo "4️⃣ 測試ReDoc文檔..."
if curl -f -s "$SERVICE_URL/redoc" > /dev/null; then
    echo "✅ ReDoc文檔可訪問"
    echo "📖 ReDoc: $SERVICE_URL/redoc"
else
    echo "❌ ReDoc文檔訪問失敗"
fi

echo ""

# 檢查服務狀態
echo "5️⃣ 檢查Cloud Run服務狀態..."
gcloud run services describe pill-detection-api \
    --platform managed \
    --region us-central1 \
    --format="table(
        metadata.name,
        status.conditions[0].type,
        status.conditions[0].status,
        status.url
    )" 2>/dev/null || echo "⚠️ 無法獲取服務詳情"

echo ""

# 檢查最近的日誌
echo "6️⃣ 檢查最近的服務日誌..."
echo "📋 最近5條日誌："
gcloud logs read "resource.type=cloud_run_revision AND resource.labels.service_name=pill-detection-api" \
    --limit=5 \
    --format="table(timestamp,severity,textPayload)" 2>/dev/null || echo "⚠️ 無法獲取日誌"

echo ""
echo "🎉 部署測試完成！"
echo ""
echo "📋 快速鏈接："
echo "🌐 服務首頁: $SERVICE_URL"
echo "📚 API文檔: $SERVICE_URL/docs"
echo "📖 ReDoc: $SERVICE_URL/redoc"
echo "🔍 健康檢查: $SERVICE_URL/health"
echo ""
echo "💡 提示："
echo "- 如果是首次部署，模型加載可能需要30秒"
echo "- 可以使用 'gcloud logs tail' 查看實時日誌"
echo "- 測試藥丸檢測功能請訪問API文檔頁面"
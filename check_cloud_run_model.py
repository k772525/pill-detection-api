#!/usr/bin/env python3
"""
檢查 Cloud Run 上的模型下載和載入狀況
"""
import requests
import json

# Cloud Run 服務 URL（需要替換為實際的 URL）
SERVICE_URL = "https://pill-detection-api-712800774423.us-central1.run.app"

def check_model_status():
    """檢查模型載入狀態"""
    try:
        # 檢查健康狀態
        print("🔍 檢查服務健康狀態...")
        health_response = requests.get(f"{SERVICE_URL}/health", timeout=30)
        print(f"健康檢查狀態: {health_response.status_code}")
        if health_response.status_code == 200:
            print("✅ 服務正常運行")
        else:
            print("❌ 服務異常")
            return
        
        # 檢查模型資訊
        print("\n📋 檢查模型資訊...")
        try:
            # 使用正確的模型端點
            model_response = requests.get(f"{SERVICE_URL}/api/models", timeout=30)
            if model_response.status_code == 200:
                model_info = model_response.json()
                print(f"模型狀態: {json.dumps(model_info, indent=2, ensure_ascii=False)}")
                
                # 檢查模型是否成功載入
                if model_info.get('success') and model_info.get('data', {}).get('loaded_models'):
                    loaded_models = model_info['data']['loaded_models']
                    print(f"\n✅ 已載入的模型: {list(loaded_models.keys())}")
                    for model_name, model_status in loaded_models.items():
                        if model_status:
                            print(f"  ✅ {model_name}: 載入成功")
                        else:
                            print(f"  ❌ {model_name}: 載入失敗")
                else:
                    print("❌ 沒有模型成功載入")
            else:
                print(f"無法獲取模型狀態 (HTTP {model_response.status_code})")
        except requests.exceptions.RequestException as e:
            print(f"模型狀態端點無法訪問: {e}")
        
        # 測試一個簡單的檢測請求
        print("\n🧪 測試檢測功能...")
        try:
            test_response = requests.get(f"{SERVICE_URL}/docs", timeout=30)
            if test_response.status_code == 200:
                print("✅ API 文檔可訪問")
            else:
                print(f"❌ API 文檔無法訪問 (HTTP {test_response.status_code})")
        except requests.exceptions.RequestException as e:
            print(f"❌ 測試請求失敗: {e}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ 連接失敗: {e}")
        print("💡 請確認:")
        print("   1. Cloud Run 服務是否成功部署")
        print("   2. 服務 URL 是否正確")
        print("   3. 服務是否允許未驗證訪問")

def get_service_url():
    """提供獲取服務 URL 的指令"""
    print("📝 獲取實際服務 URL 的指令:")
    print("gcloud run services describe pill-detection-api \\")
    print("  --platform managed --region us-central1 \\")
    print("  --format 'value(status.url)'")
    print()
    print("或者檢查 GitHub Actions 日誌中的部署輸出")

if __name__ == "__main__":
    print("🚀 檢查 Cloud Run 上的藥丸檢測 API")
    print("=" * 50)
    
    get_service_url()
    print()
    
    # 檢查是否有實際的服務 URL
    if "YOUR_HASH" in SERVICE_URL:
        print("⚠️  請先更新 SERVICE_URL 為實際的 Cloud Run 服務 URL")
        print("   然後重新運行此腳本")
    else:
        check_model_status()
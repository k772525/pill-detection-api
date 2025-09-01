from fastapi import FastAPI, HTTPException, UploadFile, File, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import time
import uuid
import traceback
import os
import io
import base64
from PIL import Image
import logging

from datetime import datetime
import uvicorn

# 設置結構化日誌
import json
import sys
from datetime import datetime

class StructuredLogger:
    def __init__(self, name):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
        
        # 創建格式化器
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # 控制台處理器
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
    
    def info(self, message, **kwargs):
        self._log('INFO', message, **kwargs)
    
    def error(self, message, **kwargs):
        self._log('ERROR', message, **kwargs)
    
    def warning(self, message, **kwargs):
        self._log('WARNING', message, **kwargs)
    
    def debug(self, message, **kwargs):
        self._log('DEBUG', message, **kwargs)
    
    def _log(self, level, message, **kwargs):
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': level,
            'message': message,
            'service': 'pill-detection-api',
            **kwargs
        }
        
        if level == 'ERROR':
            self.logger.error(json.dumps(log_data, ensure_ascii=False))
        elif level == 'WARNING':
            self.logger.warning(json.dumps(log_data, ensure_ascii=False))
        elif level == 'DEBUG':
            self.logger.debug(json.dumps(log_data, ensure_ascii=False))
        else:
            self.logger.info(json.dumps(log_data, ensure_ascii=False))

logger = StructuredLogger(__name__)

# 創建FastAPI應用
app = FastAPI(
    title="藥丸檢測API",
    description="使用YOLO模型進行藥丸檢測的FastAPI應用",
    version="2.0.1",  # 小版本升級
    docs_url="/docs",
    redoc_url="/redoc"
)

# 請求追蹤中間件
@app.middleware("http")
async def request_tracking_middleware(request: Request, call_next):
    """請求追蹤和性能監控中間件"""
    # 生成請求ID
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    
    # 記錄請求開始
    start_time = time.time()
    
    logger.info(
        "Request started",
        request_id=request_id,
        method=request.method,
        url=str(request.url),
        client_ip=request.client.host if request.client else "unknown"
    )
    
    try:
        # 處理請求
        response = await call_next(request)
        
        # 計算處理時間
        process_time = time.time() - start_time
        
        # 記錄請求完成
        logger.info(
            "Request completed",
            request_id=request_id,
            status_code=response.status_code,
            process_time=round(process_time, 4)
        )
        
        # 添加請求ID到響應頭
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = str(round(process_time, 4))
        
        return response
        
    except Exception as e:
        # 記錄請求錯誤
        process_time = time.time() - start_time
        logger.error(
            "Request failed",
            request_id=request_id,
            error=str(e),
            process_time=round(process_time, 4),
            traceback=traceback.format_exc()
        )
        raise

# 添加CORS中間件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生產環境中應該設置具體的域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全域異常處理器
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """HTTP異常處理器"""
    request_id = getattr(request.state, 'request_id', 'unknown')
    
    logger.error(
        "HTTP Exception",
        request_id=request_id,
        status_code=exc.status_code,
        detail=exc.detail,
        url=str(request.url)
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": exc.detail,
            "request_id": request_id,
            "timestamp": datetime.utcnow().isoformat()
        }
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """請求驗證異常處理器"""
    request_id = getattr(request.state, 'request_id', 'unknown')
    
    logger.error(
        "Validation Error",
        request_id=request_id,
        errors=exc.errors(),
        url=str(request.url)
    )
    
    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "error": "請求參數驗證失敗",
            "details": exc.errors(),
            "request_id": request_id,
            "timestamp": datetime.utcnow().isoformat()
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """通用異常處理器"""
    request_id = getattr(request.state, 'request_id', 'unknown')
    
    logger.error(
        "Unhandled Exception",
        request_id=request_id,
        error=str(exc),
        error_type=type(exc).__name__,
        url=str(request.url),
        traceback=traceback.format_exc()
    )
    
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "內部伺服器錯誤",
            "request_id": request_id,
            "timestamp": datetime.utcnow().isoformat()
        }
    )

# 全域變數來存儲模型
models_loaded = False
loaded_models = {}

# Pydantic模型定義
class DetectionRequest(BaseModel):
    """檢測請求模型"""
    image: str = Field(..., description="Base64編碼的圖片")
    model_name: Optional[str] = Field(None, description="指定使用的模型名稱")

class SimpleDetectionRequest(BaseModel):
    """簡化檢測請求模型"""
    image: str = Field(..., description="Base64編碼的圖片")
    model_name: Optional[str] = Field(None, description="指定使用的模型名稱")

class HealthResponse(BaseModel):
    """健康檢查響應模型"""
    status: str
    timestamp: str
    models_loaded: bool
    available_models: List[str]
    services: Dict[str, Any] = {}

class DetectionResponse(BaseModel):
    """檢測響應模型"""
    success: bool
    detections: List[Dict[str, Any]]
    pills_info: List[Dict[str, Any]]
    annotated_image_url: Optional[str]
    elapsed_time: float
    model_name: str
    message: Optional[str] = None

class SimpleDetectionResponse(BaseModel):
    """簡化檢測響應模型"""
    success: bool
    detections: List[Dict[str, Any]]
    elapsed_time: float
    model_name: str

class ModelsResponse(BaseModel):
    """模型列表響應模型"""
    success: bool
    available_models: List[str]

# 應用啟動和關閉事件
@app.on_event("startup")
async def startup_event():
    """應用啟動時的初始化"""
    logger.info("🚀 FastAPI應用啟動中...")
    await initialize_models_async()

@app.on_event("shutdown")
async def shutdown_event():
    """應用關閉時的清理"""
    logger.info("🛑 FastAPI應用關閉中...")

# 模型管理函數
async def initialize_models_async():
    """異步初始化模型"""
    global models_loaded, loaded_models
    
    try:
        logger.info("正在初始化YOLO模型...")
        
        # 導入相關模組
        from modules.yolo_pill_analyzer import initialize_models as init_yolo_models
        from modules.yolo_pill_analyzer import get_available_models
        
        # 初始化模型
        init_yolo_models()
        
        # 初始化資料庫連線池
        logger.info("正在初始化資料庫連線池...")
        from db_cloud_sql import get_db_connection_pool
        db_pool = get_db_connection_pool()
        if db_pool:
            logger.info("✅ 資料庫連線池初始化成功")
        else:
            logger.error("❌ 資料庫連線池初始化失敗，請檢查環境變數設定與日誌")
        
        # 檢查可用模型
        available_models = get_available_models()
        logger.info(f"可用模型: {available_models}")
        
        models_loaded = True
        logger.info("✅ 模型初始化完成")
        
    except Exception as e:
        logger.error(f"❌ 模型初始化失敗: {str(e)}")
        models_loaded = False

def get_available_models():
    """獲取可用模型列表"""
    try:
        if not models_loaded:
            return []
        
        from modules.yolo_pill_analyzer import get_available_models as get_models
        return get_models()
    except Exception as e:
        logger.error(f"獲取模型列表失敗: {str(e)}")
        return []

def detect_pills_internal(model_name, image_pil):
    """內部檢測函數"""
    try:
        if not models_loaded:
            return {'error': '模型尚未載入'}
        
        from modules.yolo_pill_analyzer import detect_pills
        return detect_pills(model_name, image_pil)
    except Exception as e:
        logger.error(f"檢測失敗: {str(e)}")
        return {'error': f'檢測過程中發生錯誤: {str(e)}'}

def create_annotated_image_internal(image_pil, detections, pills_info):
    """內部圖片標註函數"""
    try:
        if not models_loaded:
            print("[調試] 模型未載入，跳過圖片標註")
            return None
        
        print(f"[調試] 開始調用 create_and_upload_annotated_image")
        print(f"[調試] 參數 - 檢測數量: {len(detections)}, 藥品資訊: {len(pills_info)}")
        
        from modules.yolo_pill_analyzer import create_and_upload_annotated_image
        result = create_and_upload_annotated_image(image_pil, detections, pills_info)
        
        print(f"[調試] create_and_upload_annotated_image 返回結果: {result}")
        return result
    except Exception as e:
        logger.error(f"圖片標註失敗: {str(e)}")
        print(f"[調試] 圖片標註異常: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

async def ensure_models_loaded():
    """確保模型已載入"""
    global models_loaded
    if not models_loaded:
        await initialize_models_async()

# API端點定義
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    健康檢查端點
    檢查應用狀態、模型載入狀態和各服務狀態
    """
    try:
        available_models = get_available_models()
        
        # 檢查各服務狀態
        services = {}
        
        # 檢查模型狀態
        services['models'] = {
            'status': 'ok' if models_loaded and available_models else 'error',
            'count': len(available_models),
            'models': available_models
        }
        
        # 檢查資料庫連線
        try:
            from db_cloud_sql import get_db_connection_pool
            pool = get_db_connection_pool()
            services['database'] = {
                'status': 'ok' if pool else 'error'
            }
        except Exception as e:
            services['database'] = {
                'status': 'error',
                'error': str(e)
            }
        
        return HealthResponse(
            status='healthy' if models_loaded else 'degraded',
            timestamp=datetime.utcnow().isoformat(),
            models_loaded=models_loaded,
            available_models=available_models,
            services=services
        )
    except Exception as e:
        logger.error(f"健康檢查失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=f"健康檢查失敗: {str(e)}")

@app.get("/api/models", response_model=ModelsResponse)
async def get_models():
    """
    獲取可用模型列表
    """
    try:
        models = get_available_models()
        return ModelsResponse(
            success=True,
            available_models=models
        )
    except Exception as e:
        logger.error(f"獲取模型列表錯誤: {str(e)}")
        raise HTTPException(status_code=500, detail=f"獲取模型列表失敗: {str(e)}")

@app.post("/api/detect", response_model=DetectionResponse)
async def detect_pills_api(request: DetectionRequest, http_request: Request):
    """
    藥丸檢測API端點
    上傳圖片進行藥丸檢測，返回檢測結果、藥品資訊和標註圖片
    """
    request_id = getattr(http_request.state, 'request_id', 'unknown')
    
    try:
        logger.info("Starting pill detection", request_id=request_id)
        
        # 確保模型已載入
        await ensure_models_loaded()
        
        # 檢查模型是否已載入
        if not models_loaded:
            logger.error("Models not loaded", request_id=request_id)
            raise HTTPException(status_code=503, detail="模型尚未載入，請稍後再試")
        
        # 獲取模型名稱
        model_name = request.model_name
        available_models = get_available_models()
        
        logger.info(
            "Model selection", 
            request_id=request_id,
            requested_model=model_name,
            available_models=available_models
        )
        
        if not available_models:
            logger.error("No available models", request_id=request_id)
            raise HTTPException(status_code=500, detail="沒有可用的模型")
        
        if model_name is None:
            model_name = available_models[0]  # 使用第一個可用模型
            logger.info("Using default model", request_id=request_id, model_name=model_name)
        elif model_name not in available_models:
            logger.error(
                "Invalid model requested", 
                request_id=request_id,
                requested_model=model_name,
                available_models=available_models
            )
            raise HTTPException(
                status_code=400, 
                detail=f"模型 {model_name} 不可用，可用模型: {available_models}"
            )
        
        # 解碼base64圖片
        try:
            logger.info("Decoding image", request_id=request_id)
            image_data = base64.b64decode(request.image)
            image_pil = Image.open(io.BytesIO(image_data))
            
            logger.info(
                "Image decoded successfully", 
                request_id=request_id,
                image_size=image_pil.size,
                image_mode=image_pil.mode
            )
            
            if image_pil.mode in ('RGBA', 'LA', 'P'):
                image_pil = image_pil.convert('RGB')
                logger.info("Image converted to RGB", request_id=request_id)
                
        except Exception as e:
            logger.error(
                "Image decoding failed", 
                request_id=request_id,
                error=str(e)
            )
            raise HTTPException(status_code=400, detail=f"圖片解碼失敗: {str(e)}")
        
        # 執行YOLO檢測
        logger.info("Starting YOLO detection", request_id=request_id, model_name=model_name)
        detection_result = detect_pills_internal(model_name, image_pil)
        
        if 'error' in detection_result:
            logger.error(
                "Detection failed", 
                request_id=request_id,
                error=detection_result['error']
            )
            raise HTTPException(status_code=500, detail=detection_result['error'])
        
        detections = detection_result['detections']
        elapsed_time = detection_result['elapsed_time']
        
        logger.info(
            "Detection completed", 
            request_id=request_id,
            detections_count=len(detections),
            elapsed_time=elapsed_time
        )
        
        # 如果沒有檢測到任何藥丸
        if not detections:
            logger.info("No pills detected", request_id=request_id)
            return DetectionResponse(
                success=True,
                detections=[],
                pills_info=[],
                annotated_image_url=None,
                elapsed_time=elapsed_time,
                model_name=model_name,
                message='未檢測到任何藥丸'
            )
        
        # 獲取檢測到的藥丸ID列表
        detected_drug_ids = [det['class_name'] for det in detections]
        
        # 從資料庫獲取藥丸資訊
        pills_info_from_db = []
        try:
            logger.info(
                "Querying database for pill information", 
                request_id=request_id,
                detected_drug_ids=detected_drug_ids,
                model_name=model_name
            )
            
            from db_cloud_sql import get_pills_details_by_ids
            pills_info_from_db = get_pills_details_by_ids(detected_drug_ids, model_name)
            
            logger.info(
                "Database query completed", 
                request_id=request_id,
                pills_found=len(pills_info_from_db)
            )
            
        except Exception as e:
            logger.warning(
                "Failed to get pill information from database", 
                request_id=request_id,
                error=str(e),
                traceback=traceback.format_exc()
            )
        
        # 創建並上傳標註圖片（包含中文標籤）
        logger.info(
            "Creating annotated image", 
            request_id=request_id,
            detections_count=len(detections),
            pills_info_count=len(pills_info_from_db)
        )
        
        annotated_image_url = create_annotated_image_internal(
            image_pil, detections, pills_info_from_db
        )
        
        logger.info(
            "Annotated image created", 
            request_id=request_id,
            image_url=annotated_image_url
        )
        
        logger.info(
            "Detection API completed successfully", 
            request_id=request_id,
            total_detections=len(detections),
            total_pills_info=len(pills_info_from_db)
        )
        
        return DetectionResponse(
            success=True,
            detections=detections,
            pills_info=pills_info_from_db,
            annotated_image_url=annotated_image_url,
            elapsed_time=elapsed_time,
            model_name=model_name
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Unexpected error in detection API", 
            request_id=request_id,
            error=str(e),
            error_type=type(e).__name__,
            traceback=traceback.format_exc()
        )
        raise HTTPException(status_code=500, detail=f"內部伺服器錯誤: {str(e)}")

@app.post("/api/detect/simple", response_model=SimpleDetectionResponse)
async def detect_pills_simple(request: SimpleDetectionRequest):
    """
    簡化版檢測API，只返回檢測結果，不創建標註圖片
    適用於只需要檢測結果的場景，響應更快
    """
    try:
        # 確保模型已載入
        await ensure_models_loaded()
        
        # 檢查模型是否已載入
        if not models_loaded:
            raise HTTPException(status_code=503, detail="模型尚未載入，請稍後再試")
        
        # 獲取模型名稱
        model_name = request.model_name
        available_models = get_available_models()
        
        if not available_models:
            raise HTTPException(status_code=500, detail="沒有可用的模型")
        
        if model_name is None:
            model_name = available_models[0]
        elif model_name not in available_models:
            raise HTTPException(
                status_code=400,
                detail=f"模型 {model_name} 不可用，可用模型: {available_models}"
            )
        
        # 解碼圖片
        try:
            image_data = base64.b64decode(request.image)
            image_pil = Image.open(io.BytesIO(image_data))
            if image_pil.mode in ('RGBA', 'LA', 'P'):
                image_pil = image_pil.convert('RGB')
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"圖片解碼失敗: {str(e)}")
        
        # 執行檢測
        detection_result = detect_pills_internal(model_name, image_pil)
        
        if 'error' in detection_result:
            raise HTTPException(status_code=500, detail=detection_result['error'])
        
        return SimpleDetectionResponse(
            success=True,
            detections=detection_result['detections'],
            elapsed_time=detection_result['elapsed_time'],
            model_name=model_name
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"簡化檢測API錯誤: {str(e)}")
        raise HTTPException(status_code=500, detail=f"內部伺服器錯誤: {str(e)}")

@app.post("/api/detect/upload")
async def detect_pills_upload(file: UploadFile = File(...), model_name: Optional[str] = None):
    """
    通過文件上傳進行藥丸檢測
    支持直接上傳圖片文件
    """
    try:
        # 確保模型已載入
        await ensure_models_loaded()
        
        if not models_loaded:
            raise HTTPException(status_code=503, detail="模型尚未載入，請稍後再試")
        
        # 檢查文件類型
        if not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="只支持圖片文件")
        
        # 讀取圖片
        try:
            image_data = await file.read()
            image_pil = Image.open(io.BytesIO(image_data))
            if image_pil.mode in ('RGBA', 'LA', 'P'):
                image_pil = image_pil.convert('RGB')
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"圖片讀取失敗: {str(e)}")
        
        # 獲取模型名稱
        available_models = get_available_models()
        if not available_models:
            raise HTTPException(status_code=500, detail="沒有可用的模型")
        
        if model_name is None:
            model_name = available_models[0]
        elif model_name not in available_models:
            raise HTTPException(
                status_code=400,
                detail=f"模型 {model_name} 不可用，可用模型: {available_models}"
            )
        
        # 執行檢測
        detection_result = detect_pills_internal(model_name, image_pil)
        
        if 'error' in detection_result:
            raise HTTPException(status_code=500, detail=detection_result['error'])
        
        return {
            "success": True,
            "filename": file.filename,
            "detections": detection_result['detections'],
            "elapsed_time": detection_result['elapsed_time'],
            "model_name": model_name
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"文件上傳檢測錯誤: {str(e)}")
        raise HTTPException(status_code=500, detail=f"內部伺服器錯誤: {str(e)}")

# 根路徑
@app.get("/")
async def root():
    """根路徑，返回API資訊"""
    return {
        "message": "藥丸檢測API - FastAPI版本",
        "version": "2.0.0",
        "docs": "/docs",
        "health": "/health",
        "models": "/api/models"
    }

if __name__ == "__main__":
    # 本地開發時使用
    print("🚀 啟動FastAPI本地開發服務器...")
    port = int(os.environ.get('PORT', 8080))
    print(f"📡 服務器將在 http://localhost:{port} 啟動")
    print(f"📖 API文檔: http://localhost:{port}/docs")
    
    uvicorn.run(
        "fastapi_app:app",
        host="0.0.0.0",
        port=port,
        reload=True,  # 開發模式下自動重載
        log_level="info"
    )
import os
import time
import uuid
import logging
from PIL import  ImageDraw, ImageFont
from ultralytics import YOLO
import re
# 配置日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 嘗試導入 Google Cloud Storage，如果失敗則跳過
try:
    from google.cloud import storage
    GCS_AVAILABLE = True
    logger.info("[調試] Google Cloud Storage 可用")
except ImportError:
    GCS_AVAILABLE = False
    logger.info("[調試] Google Cloud Storage 不可用，將使用本地儲存")

# --- GCS 和模型設定 ---
GCS_BUCKET_NAME = os.environ.get("GCS_BUCKET_NAME")
MODEL_PATHS = {"YOLOv12.pt": "models/YOLOv12.pt"}

loaded_models = {}

# 延遲初始化 GCS client（避免啟動時認證錯誤）
client = None
bucket = None

# --- 全域顏色設定 ---
COLORS = ["#FF6B6B", "#4ECDC4", "#45B7D1", "#F9A825", "#6A89CC", "#E84393", "#079992"]

def get_color_for_index(i):
    """根據索引回傳固定順序的顏色"""
    return COLORS[i % len(COLORS)]

def initialize_models():
    """在應用程式啟動時載入所有指定的 YOLO 模型。"""
    logger.info("YOLO Analyzer - 開始載入 YOLO 模型...")
    for model_display_name, model_file_path in MODEL_PATHS.items():
        if not os.path.exists(model_file_path):
            logger.warning(f"警告: 模型檔案 '{model_file_path}' 不存在，跳過。")
            loaded_models[model_display_name] = None
            continue
        try:
            loaded_models[model_display_name] = YOLO(model_file_path)
            logger.info(f"成功載入模型: '{model_display_name}'")
        except Exception as e:
            logger.warning(f"警告: 載入模型 '{model_display_name}' 失敗: {e}")
            loaded_models[model_display_name] = None
    logger.info("YOLO Analyzer - 模型載入完成。")


def upload_file_to_gcs(local_file_path, bucket_name, object_name=None):
    """將本地檔案上傳到 Google Cloud Storage 儲存桶，並回傳公開存取 URL。"""
    if not GCS_AVAILABLE:
        logger.info("[調試] GCS 不可用，跳過上傳")
        return None
        
    if object_name is None:
        object_name = os.path.basename(local_file_path)

    try:
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(object_name)
        blob.upload_from_filename(local_file_path)
        public_url = blob.public_url
        return public_url
    except Exception as e:
        logger.error(f"GCS 上傳時發生錯誤: {e}")
        return None

def _draw_custom_labels(base_image, detections, pills_info_from_db):
    """【樣式優化 v4】精準對齊文字與背景 + 保證每個框顏色不重複"""

    print("--- 開始建立中文標籤映射 ---")
    print(f"原始藥品資訊 (pills_info_from_db): {pills_info_from_db}")

    # 步驟 1: 建立從 drug_id (英文) 到中文名稱的映射字典。
    name_map = {}
    for pill in pills_info_from_db:
        drug_id = pill['drug_id']
        drug_name_zh = pill.get('drug_name_zh', drug_id)
        
        # 使用正規表達式偵測數字以前的中文字
        if drug_name_zh != drug_id:
            # 移除引號，然後匹配中文字符直到遇到數字或括號
            clean_name = drug_name_zh.replace('"', '').replace('"', '').replace('"', '')
            match = re.match(r'^([^\d\(\uff08]*[\u4e00-\u9fff][^\d\(\uff08]*)', clean_name)
            if match:
                drug_name_zh = match.group(1).strip()
        
        name_map[drug_id] = drug_name_zh
        print(f"  映射: drug_id='{drug_id}' -> 中文名稱='{drug_name_zh}' (是否有中文: {'是' if drug_name_zh != drug_id else '否'})")
    print(f"最終中文標籤映射 (name_map): {name_map}")
    print("--- 中文標籤映射建立完成 ---")
    
    # 額外調試：檢測到的藥品ID
    print("\n=== 檢測到的藥品ID列表 ===")
    for i, det in enumerate(detections):
        print(f"檢測 {i+1}: '{det['class_name']}'")
    print("=========================")
    # 調試輸出
    logger.info(f"[調試] 檢測到的藥品: {[det['class_name'] for det in detections]}")
    logger.info(f"[調試] 資料庫藥品: {list(name_map.keys())}")
    logger.info(f"[調試] 中文名稱映射: {name_map})")
    # 步驟 2: 準備繪圖
    editable_image = base_image.copy().convert("RGB")
    draw = ImageDraw.Draw(editable_image)

    # --- 測試：解決文字框重疊問題＆避免超出圖片邊緣 ---
    # 最前面要多「from PIL import Image」

    occupied_areas = []     # 用個List儲存已放置的文字框位置

    image_width, image_height = editable_image.size

    def boxes_overlap(a, b):
        """判斷兩個文字方塊是否重疊"""
        ax0, ay0, ax1, ay1 = a
        bx0, by0, bx1, by1 = b
        return not (ax1 <= bx0 or ax0 >= bx1 or ay1 <= by0 or ay0 >= by1)
    
    # 步驟 3: 載入支援中文的字型檔 (改進版)
    font_size = max(25, int(base_image.width / 25))
    font = None
    
    # 字型檔案優先順序列表
    font_paths = [
        "fonts/jf-openhuninn-2.1.ttf",           # 主要字型
        "fonts/NotoSansCJK-Regular.ttc",         # Google Noto 備用
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",  # 系統 Noto
        "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",           # 系統文泉驛
        "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",         # 系統文泉驛微米黑
    ]
    
    for font_path in font_paths:
        try:
            if os.path.exists(font_path):
                font = ImageFont.truetype(font_path, font_size)
                logger.info(f"✅ 成功載入字型: {font_path}")
                break
        except Exception as e:
            logger.debug(f"字型載入失敗 {font_path}: {str(e)}")
            continue
    
    if font is None:
        logger.warning("⚠️ 所有中文字型載入失敗，使用預設字型 (中文可能無法正確顯示)")
        font = ImageFont.load_default()

    # --- 使用全域顏色函數 ---

    # --- 繪圖 ---
    for i, det in enumerate(detections):
        bbox = det['bbox']      # [x0, y0, x1, y1]
        drug_id = det['class_name']
        
        # 使用正規表達式移除各種後綴來匹配資料庫中的藥品ID
        base_drug_id = drug_id
        # 匹配並移除 _ 後面的所有內容
        pattern = r'_.*$'
        match = re.search(pattern, drug_id)
        if match:
            base_drug_id = re.sub(pattern, '', drug_id)

            print(f"    後綴處理: '{drug_id}' -> '{base_drug_id}' (移除後綴: '{match.group(0)}')")
        
        label_text = name_map.get(base_drug_id, drug_id)
        
        # 詳細的匹配調試
        print(f"\n--- 藥品 {i+1} 標籤匹配過程 ---")
        print(f"原始檢測ID: '{drug_id}'")
        print(f"處理後基礎ID: '{base_drug_id}'")
        print(f"在映射字典中查找: {base_drug_id in name_map}")
        if base_drug_id in name_map:
            print(f"找到匹配! 中文名稱: '{name_map[base_drug_id]}'")
        else:
            print(f"未找到匹配，使用原ID: '{drug_id}'")
            print(f"可用的映射鍵: {list(name_map.keys())}")
        print(f"最終標籤文字: '{label_text}'")
        print(f"顯示類型: {'中文標籤' if label_text != drug_id and label_text != base_drug_id else '英文ID'}")
        print("--------------------------------")
        
        logger.info(f"[調試] 檢測藥品: {drug_id} -> 基礎ID: {base_drug_id} -> 中文標籤: {label_text}")
        box_color = get_color_for_index(i)
        text_color = "#000000"
        bg_color = box_color

        # 繪製矩形框
        draw.rectangle(bbox, outline=box_color, width=4)

        # 1. 定義水平和垂直的 padding
        h_padding = 5
        v_padding = 3
        # 2. 取得文字的精確尺寸
        if hasattr(draw, 'textbbox'):
            text_bbox = draw.textbbox((0, 0), label_text, font=font)
            text_width = text_bbox[2] - text_bbox[0]
            text_height = text_bbox[3] - text_bbox[1]
        else:
            text_width, text_height = draw.textsize(label_text, font=font)
        
        # 3. 確保文字框不會超出圖片邊界
        max_text_width = image_width - 2 * h_padding
        if text_width > max_text_width:
            # 如果文字太長，縮小字型
            scale_factor = max_text_width / text_width
            new_font_size = max(12, int(font_size * scale_factor))
            try:
                if hasattr(font, 'path'):
                    font = ImageFont.truetype(font.path, new_font_size)
                else:
                    font = ImageFont.load_default()
                # 重新計算文字尺寸
                if hasattr(draw, 'textbbox'):
                    text_bbox = draw.textbbox((0, 0), label_text, font=font)
                    text_width = text_bbox[2] - text_bbox[0]
                    text_height = text_bbox[3] - text_bbox[1]
                else:
                    text_width, text_height = draw.textsize(label_text, font=font)
            except:
                # 如果字型調整失敗，使用預設字型
                font = ImageFont.load_default()
                if hasattr(draw, 'textbbox'):
                    text_bbox = draw.textbbox((0, 0), label_text, font=font)
                    text_width = text_bbox[2] - text_bbox[0]
                    text_height = text_bbox[3] - text_bbox[1]
                else:
                    text_width, text_height = draw.textsize(label_text, font=font)

        # 候選位置：優先靠近檢測框的位置
        candidate_offsets = [
            (bbox[0], bbox[1] - (text_height + 2 * v_padding)),  # 上方緊貼
            (bbox[0], bbox[3] + 2),                              # 下方緊貼
            (bbox[2] - (text_width + 2 * h_padding), bbox[1] - (text_height + 2 * v_padding)), # 右上
            (bbox[2] - (text_width + 2 * h_padding), bbox[3] + 2), # 右下
            (bbox[0] - (text_width + 2 * h_padding), bbox[1]),     # 左側
            (bbox[2] + 2, bbox[1]),                                # 右側
        ]

        # 縮小搜索範圍，讓標籤更接近檢測框
        max_offset = min(30, text_width // 2)  # 最大偏移距離限制為30像素或文字寬度的一半
        step_size = 8  # 增大步長，減少計算量
        candidates = []

        for base_x, base_y in candidate_offsets:
            # 每個基礎位置嘗試少量偏移
            for offset_x in range(0, max_offset, step_size):
                for direction in [1, -1]:  # 向右和向左
                    tx0 = base_x + (offset_x * direction)
                    ty0 = base_y
                    tx1 = tx0 + text_width + 2 * h_padding
                    ty1 = ty0 + text_height + 2 * v_padding

                    # 確保文字框完全在圖片邊界內
                    if tx0 < 0 or ty0 < 0 or tx1 > image_width or ty1 > image_height:
                        continue

                    label_box = (tx0, ty0, tx1, ty1)

                    if not any(boxes_overlap(label_box, occ) for occ in occupied_areas):
                        # 計算距離檢測框的距離，越近越好
                        center_x = bbox[0] + (bbox[2] - bbox[0]) // 2
                        center_y = bbox[1] + (bbox[3] - bbox[1]) // 2
                        label_center_x = tx0 + (text_width + 2 * h_padding) // 2
                        label_center_y = ty0 + (text_height + 2 * v_padding) // 2
                        distance = ((center_x - label_center_x) ** 2 + (center_y - label_center_y) ** 2) ** 0.5
                        
                        # 優先級：上方 > 下方 > 左右側 > 其他
                        position_priority = 0
                        if ty1 <= bbox[1] + 5:  # 上方（允許小量重疊）
                            position_priority = 0
                        elif ty0 >= bbox[3] - 5:  # 下方（允許小量重疊）
                            position_priority = 1
                        elif tx1 <= bbox[0] + 5 or tx0 >= bbox[2] - 5:  # 左右側
                            position_priority = 2
                        else:  # 其他位置
                            position_priority = 3
                        
                        candidates.append({
                            'box': label_box,
                            'text_pos': (tx0 + h_padding, ty0 + v_padding),
                            'score': (position_priority, distance)
                        })

        if candidates:
            # 按照優先條件排序並選第一個（tuple 自然排序：False < True）
            best = sorted(candidates, key=lambda c: c['score'])[0]
            (bg_x0, bg_y0, bg_x1, bg_y1) = best['box']
            text_x, text_y = best['text_pos']
            occupied_areas.append((bg_x0, bg_y0, bg_x1, bg_y1))
        else:
            # 最壞情況的fallback: 強制放在圖片邊界內，避免超出
            bg_x0 = max(0, min(bbox[0], image_width - (text_width + 2 * h_padding)))
            bg_y0 = max(0, min(bbox[1] - (text_height + 2 * v_padding), image_height - (text_height + 2 * v_padding)))
            bg_x1 = bg_x0 + text_width + (2 * h_padding)
            bg_y1 = bg_y0 + text_height + (2 * v_padding)
            
            # 再次確保不超出邊界
            if bg_x1 > image_width:
                bg_x1 = image_width
                bg_x0 = bg_x1 - (text_width + 2 * h_padding)
            if bg_y1 > image_height:
                bg_y1 = image_height
                bg_y0 = bg_y1 - (text_height + 2 * v_padding)
                
            text_x = bg_x0 + h_padding
            text_y = bg_y0 + v_padding
            occupied_areas.append((bg_x0, bg_y0, bg_x1, bg_y1))
        
        # 繪製文字背景
        draw.rectangle((bg_x0, bg_y0, bg_x1, bg_y1), fill=bg_color)
        # 繪製文字
        draw.text((text_x, text_y), label_text, fill=text_color, font=font)
    return editable_image

def detect_pills(model_name, image_pil):
    
    # 記錄開始時間用於計算處理耗時
    start_time = time.time()
    
    # 檢查模型是否已載入並可用
    if model_name not in loaded_models or loaded_models[model_name] is None:
        return {'error': f"模型 '{model_name}' 未載入"}
    
    # 獲取模型物件
    model_object = loaded_models[model_name]
    
    try:
        # 使用 YOLO 模型進行預測，設定信心度閾值為 0.7
        results = model_object.predict(source=image_pil, conf=0.7)
        result = results[0]  # 取得第一張圖片的結果
        
        # 初始化偵測結果列表
        detections = []
        
        # 遍歷所有檢測到的物件
        for i in range(len(result.boxes)):
            detections.append({
                'class_name': model_object.names[int(result.boxes.cls[i])],  # 類別名稱
                'confidence': round(float(result.boxes.conf[i]), 3),        # 信心度（四捨五入到三位小數）
                'bbox': [round(coord) for coord in result.boxes.xyxy[i].tolist()],  # 邊界框座標
                'color': get_color_for_index(i)  # 分配對應的顏色
            })
        
        # 計算總耗時
        elapsed_time = round(time.time() - start_time, 2)
        
        # 返回完整的偵測結果
        return {
            'detections': detections, 
            'elapsed_time': elapsed_time, 
            'model_name': model_name
        }
        
    except Exception as e:
        # 記錄錯誤並返回錯誤訊息
        logger.error(f"模型 '{model_name}' 偵測時發生錯誤: {e}")
        return {'error': f'模型 "{model_name}" 偵測時內部錯誤'}

def create_and_upload_annotated_image(base_image, detections, pills_info_from_db):
    """【新函式】根據偵測結果和資料庫資訊，繪製中文標籤圖片並上傳至 GCS。"""
    logger.debug(f"[調試] 傳遞給 _draw_custom_labels 的 detections: {detections}")
    logger.debug(f"[調試] 傳遞給 _draw_custom_labels 的 pills_info_from_db: {pills_info_from_db}")
    annotated_image_pil = _draw_custom_labels(base_image, detections, pills_info_from_db)
    temp_dir = "temp_images"
    os.makedirs(temp_dir, exist_ok=True)
    local_filename = f"predicted_{uuid.uuid4().hex}.jpg"
    local_filepath = os.path.join(temp_dir, local_filename)
    gcs_object_name = f"predictions/{local_filename}"
    try:
        annotated_image_pil.save(local_filepath)
        logger.info(f"[調試] 標註圖片已保存到本地: {local_filepath}")
        
        # 檢查 GCS 配置和可用性
        if not GCS_AVAILABLE or not GCS_BUCKET_NAME:
            logger.info(f"[調試] GCS 不可用或未設定，使用本地路徑: {local_filepath}")
            return local_filepath  # 返回本地路徑
        
        logger.info(f"[調試] 開始上傳到 GCS: {GCS_BUCKET_NAME}/{gcs_object_name}")
        predict_image_url = upload_file_to_gcs(local_filepath, GCS_BUCKET_NAME, gcs_object_name)
        
        if predict_image_url:
            logger.info(f"[調試] GCS 上傳成功: {predict_image_url}")
            # 保留本地文件作為備份
            return predict_image_url
        else:
            logger.warning(f"[調試] GCS 上傳失敗，返回本地路徑: {local_filepath}")
            return local_filepath  # 返回本地路徑
            
    except Exception as e:
        logger.error(f"圖片繪製或上傳時發生錯誤: {e}")
        import traceback
        traceback.print_exc()
        return None

def get_available_models():
    """回傳已成功載入的模型名稱列表。"""
    return [name for name, model in loaded_models.items() if model is not None]

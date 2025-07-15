import os
from datetime import datetime
import logging
import sys
import sqlalchemy

# ====== Cloud Run/GCP 日誌設定 (放最上面) ======
logging.basicConfig(
    stream=sys.stdout,
    level=logging.INFO,    # 本地測試可改 DEBUG
    format='%(asctime)s %(levelname)s %(name)s %(message)s'
)
logger = logging.getLogger(__name__)

def _log_and_print(msg, level="info"):
    print(msg)
    if level == "info":
        logger.info(msg)
    elif level == "error":
        logger.error(msg)
    elif level == "debug":
        logger.debug(msg)
    elif level == "warning":
        logger.warning(msg)
    else:
        logger.info(msg)

db_pool = None

def get_db_connection_pool():
    global db_pool
    if db_pool:
        return db_pool
    try:
        db_user = os.environ["DB_USER"]
        db_pass = os.environ["DB_PASS"]
        db_name = os.environ["DB_NAME"]
        db_host = os.environ.get("DB_HOST")
        cloud_sql_conn = os.environ.get("CLOUD_SQL_CONNECTION_NAME")

        # --- Cloud Run 上部署（優先用 unix_socket）---
        if cloud_sql_conn:
            db_pool = sqlalchemy.create_engine(
                sqlalchemy.engine.url.URL.create(
                    drivername="mysql+pymysql",
                    username=db_user,
                    password=db_pass,
                    database=db_name,
                    query={"unix_socket": f"/cloudsql/{cloud_sql_conn}"},
                ),
                pool_size=5,
                max_overflow=2,
                pool_timeout=30,
                pool_recycle=1800,
            )
            _log_and_print(f"--- Google Cloud SQL 連線池 (Unix Socket: /cloudsql/{cloud_sql_conn}) 建立成功 ---")
        # --- 其他環境（本地端 TCP 連線）---
        elif db_host:
            db_pool = sqlalchemy.create_engine(
                sqlalchemy.engine.url.URL.create(
                    drivername="mysql+pymysql",
                    username=db_user,
                    password=db_pass,
                    host=db_host,
                    database=db_name,
                ),
                pool_size=5,
                max_overflow=2,
                pool_timeout=30,
                pool_recycle=1800,
            )
            _log_and_print(f"--- Google Cloud SQL 連線池 (TCP: {db_host}) 建立成功 ---")
        else:
            raise RuntimeError("[錯誤] 沒有正確指定 Cloud SQL 連線參數 (CLOUD_SQL_CONNECTION_NAME or DB_HOST)")
        return db_pool
    except KeyError as e:
        _log_and_print(f"!!!!!! [嚴重錯誤] 缺少必要的資料庫環境變數: {e} !!!!!!", level="error")
        return None
    except Exception as e:
        _log_and_print(f"!!!!!! [嚴重錯誤] 建立 Google Cloud SQL 資料庫連線池失敗: {e} !!!!!!", level="error")
        return None

def init_db_cloud_sql():
    pool = get_db_connection_pool()
    if not pool:
        _log_and_print("[錯誤] 無法取得資料庫連線池，初始化中斷。", level="error")
        return
    with pool.connect() as conn:
        _log_and_print("--- 正在檢查並建立 `health_log` 資料表 ---")
        conn.execute(sqlalchemy.text('''
            CREATE TABLE IF NOT EXISTS health_log (
                log_id INT AUTO_INCREMENT PRIMARY KEY,
                recorder_id VARCHAR(100) NOT NULL,
                target_person VARCHAR(50) NOT NULL,
                record_time DATETIME NOT NULL,
                blood_oxygen INT,
                systolic_pressure INT,
                diastolic_pressure INT,
                blood_sugar INT,
                temperature DECIMAL(5,2),
                weight DECIMAL(5,2),
                INDEX idx_recorder_id (recorder_id)
            );
        '''))
        _log_and_print("--- `health_log` 資料表檢查完成 ---")
        _log_and_print("--- 正在檢查並建立 `drug_info` 資料表 ---")
        conn.execute(sqlalchemy.text('''
            CREATE TABLE IF NOT EXISTS drug_info (
                drug_id VARCHAR(100) PRIMARY KEY,
                drug_name_en VARCHAR(255),
                drug_name_zh VARCHAR(255),
                main_use TEXT,
                side_effects TEXT,
                shape VARCHAR(100),
                color VARCHAR(100),
                food_drug_interactions TEXT,
                image_url VARCHAR(2083)
            );
        '''))
        _log_and_print("--- `drug_info` 資料表檢查完成 ---")
        conn.commit()

def get_pills_details_by_ids(drug_id, model_name=None):
    if not drug_id:
        return []
    model_info = f" (使用模型: {model_name})" if model_name else ""
    _log_and_print(f"[調試] get_pills_details_by_ids 接收到的 drug_ids: {drug_id}{model_info}")
    pool = get_db_connection_pool()
    if not pool:
        _log_and_print("[調試] 資料庫連線池不可用", level="warning")
        return []
    details_list = []
    try:
        with pool.connect() as conn:
            # 取前10碼並轉小寫
            lower_case_drug_ids = [d.lower()[:10] for d in drug_id]
            placeholders = ', '.join([':id' + str(i) for i in range(len(lower_case_drug_ids))])
            params = {'id' + str(i): lower_case_drug_ids[i] for i in range(len(lower_case_drug_ids))}
            sql = sqlalchemy.text(f"""
                SELECT drug_id, drug_name_en, drug_name_zh, main_use, side_effects, shape, color, food_drug_interactions, image_url 
                FROM drug_info WHERE LOWER(LEFT(drug_id, 10)) IN ({placeholders})
            """)
            _log_and_print(f"[調試] 執行 SQL (前10碼比對){model_info}: {sql}")
            _log_and_print(f"[調試] SQL 參數 (前10碼){model_info}: {params}")
            results = conn.execute(sql, params)
            rows = results.fetchall()
            _log_and_print(f"[調試] 資料庫查詢返回 {len(rows)} 筆記錄{model_info}")
            for row in rows:
                row_dict = dict(row._mapping)
                details_list.append({
                    'drug_id': row_dict.get('drug_id'),
                    'drug_name_en': row_dict.get('drug_name_en'),
                    'drug_name_zh': row_dict.get('drug_name_zh'),
                    'uses': row_dict.get('main_use'),
                    'side_effects': row_dict.get('side_effects'),
                    'shape': row_dict.get('shape'),
                    'color': row_dict.get('color'),
                    'interactions': row_dict.get('food_drug_interactions'),
                    'image_url': row_dict.get('image_url')
                })
    except Exception as e:
        _log_and_print(f"[錯誤] 查詢多筆藥品資訊時失敗: {e}", level="error")
    return details_list

def add_drug_info(drug_id, drug_name_en, drug_name_zh, main_use, side_effects, shape, color, interactions, image_url):
    pool = get_db_connection_pool()
    if not pool:
        return False
    success = False
    try:
        params = {
            "drug_id": drug_id, "drug_name_en": drug_name_en, "drug_name_zh": drug_name_zh,
            "main_use": main_use, "side_effects": side_effects, "shape": shape,
            "color": color, "interactions": interactions, "image_url": image_url
        }
        sql = sqlalchemy.text("""
            REPLACE INTO drug_info (drug_id, drug_name_en, drug_name_zh, main_use, side_effects, shape, color, food_drug_interactions, image_url)
            VALUES (:drug_id, :drug_name_en, :drug_name_zh, :main_use, :side_effects, :shape, :color, :interactions, :image_url)
        """)
        with pool.connect() as conn:
            conn.execute(sql, params)
            conn.commit()
            success = True
    except Exception as e:
        _log_and_print(f"!!!!!! [嚴重錯誤] 新增/更新藥品資訊時失敗: {e} !!!!!!", level="error")
    return success

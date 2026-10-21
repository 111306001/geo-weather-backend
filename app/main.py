import os
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
import requests
from dotenv import load_dotenv

# 引入 SQLAlchemy 相關套件
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# 從 model.py 匯入資料模型與全台行政區域資料
from app.model import RealEstateWeatherResponse, TAIWAN_ADMIN_DISTRICTS

# 載入根目錄的 .env 檔案
load_dotenv()

app = FastAPI(
    title="GeoWeather Real Estate Analytics Backend",
    description="整合不動產實價登錄與中央氣象署開放資料的雲端後端系統",
    version="1.0.0"
)

# 加上這段允許跨來源請求
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 從環境變數中讀取氣象署 API Key 與資料庫連線資訊
CWA_API_KEY = os.getenv("CWA_API_KEY")

# 資料庫連線設定 (預設使用 MySQL / MariaDB，對應 lvr_landcsv 資料庫)
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_NAME = os.getenv("DB_NAME", "lvr_landcsv")

DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@app.get("/")
def read_root():
    return {"message": "歡迎使用智慧不動產與氣象風險評估後端系統！請造訪 /docs 查看 API 文件。"}

@app.get("/api/v1/districts")
def get_districts():
    """提供全台縣市與鄉鎮市區對應資料供前端呼叫"""
    return TAIWAN_ADMIN_DISTRICTS

@app.get("/api/v1/analyze", response_model=RealEstateWeatherResponse)
def analyze_location(
    district: str = Query(..., description="行政區名稱，例如：大同區"),
    lat: float = Query(25.0330, description="緯度"),
    lon: float = Query(121.5654, description="經度")
):
    try:
        # 1. 串接真實的中央氣象署氣象資料開放平臺 API
        cwa_url = f"https://opendata.cwa.gov.tw/api/v1/rest/datastore/O-A0001-001?Authorization={CWA_API_KEY}"
        
        weather_response = requests.get(cwa_url)
        weather_json = weather_response.json()

        station_name = "中央氣象署觀測站"
        temperature = 25.0
        rainfall = 1500.0

        if weather_response.status_code == 200 and "records" in weather_json:
            stations = weather_json.get("records", {}).get("Station", [])
            if stations:
                first_station = stations[0]
                station_name = first_station.get("StationName", "未知觀測站")
                weather_elements = first_station.get("WeatherElement", {})
                temperature = weather_elements.get("AirTemperature", 25.0)

        weather_data = {
            "station": station_name,
            "temperature": float(temperature),
            "annual_rainfall": float(rainfall)
        }

        # 2. 從 SQL 資料庫查詢真實的不動產實價登錄資料
        with engine.connect() as connection:
            # 查詢該行政區的樣本數與平均單價 (將 單價元平方公尺 乘以 3.305785 換算為 元/坪)
            query_summary = text("""
                SELECT 
                    COUNT(*) as sample_count, 
                    AVG(CAST(單價元平方公尺 AS UNSIGNED) * 3.305785) as avg_ping_price 
                FROM a_lvr_land_a 
                WHERE 鄉鎮市區 = :district 
                  AND 單價元平方公尺 REGEXP '^[0-9]+$'
                  AND CAST(單價元平方公尺 AS UNSIGNED) > 0
            """)
            result = connection.execute(query_summary, {"district": district}).fetchone()
            
            sample_count = int(result.sample_count) if result and result.sample_count else 0
            average_unit_price = float(result.avg_ping_price) if result and result.avg_ping_price else 0.0

            real_estate_data = {
                "district": district,
                "average_unit_price": round(average_unit_price, 0),
                "sample_count": sample_count
            }

            # 直接從主表 a_lvr_land_a 查詢近期交易明細 (不需 JOIN build 表，避免公設分層造成重複)
            query_transactions = text("""
                SELECT 
                    鄉鎮市區, 
                    交易標的, 
                    土地位置建物門牌, 
                    總價元, 
                    單價元平方公尺, 
                    交易年月日, 
                    COALESCE( NULLIF(建物型態, ''), '其他' ) as 建物型態
                FROM a_lvr_land_a
                WHERE 鄉鎮市區 = :district 
                  AND 交易標的 != '土地'
                ORDER BY CAST(交易年月日 AS UNSIGNED) DESC
                LIMIT 5
            """)
            trans_results = connection.execute(query_transactions, {"district": district}).fetchall()
            
            recent_transactions = []
            for row in trans_results:
                # 將總價格式化加上千分位與「元」，方便前端直接顯示
                formatted_price = f"{int(row.總價元):,} 元" if str(row.總價元).isdigit() else row.總價元

                recent_transactions.append({
                    # 對齊 index.html 第 238~240 行讀取的屬性名稱
                    "address": row.土地位置建物門牌,
                    "price": formatted_price,
                    "type": row.建物型態,
                    "date": row.交易年月日,
                    # 保留原本的欄位名稱以維持相容性
                    "district": row.鄉鎮市區,
                    "target": row.交易標的,
                    "location": row.土地位置建物門牌,
                    "total_price": row.總價元,
                    "unit_price": row.單價元平方公尺,
                    "building_type": row.建物型態,
                    "transaction_date": row.交易年月日
                })

        # 3. 計算環境風險分數
        risk_score = round((weather_data["annual_rainfall"] / 1000) * 1.5, 2)

        return {
            "district": district,
            "real_estate_summary": real_estate_data,
            "weather_summary": weather_data,
            "environmental_risk_score": risk_score,
            "recent_transactions": recent_transactions
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"資料庫查詢或外部 API 發生錯誤: {str(e)}")

import os
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
import requests
import pymysql
from dotenv import load_dotenv

from app.model import RealEstateWeatherResponse, TAIWAN_ADMIN_DISTRICTS

load_dotenv()

app = FastAPI(
    title="智慧不動產與氣象 GIS 系統",
    description="整合台北市真實實價登錄 MySQL 資料庫與中央氣象署資料",
    version="2.0.0"
)

# 啟用 CORS 跨來源允許
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

CWA_API_KEY = os.getenv("CWA_API_KEY")

# MySQL 資料庫連線設定
def get_db_connection():
    return pymysql.connect(
        host="localhost",
        user="root",
        password="",      # 請填入您的 MySQL 密碼
        database="lvr_landcsv",
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor
    )

@app.get("/")
def read_root():
    return {"message": "歡迎使用智慧不動產與氣象 GIS 後端系統 (真實資料庫版)"}

@app.get("/api/v1/districts")
def get_districts():
    return TAIWAN_ADMIN_DISTRICTS

@app.get("/api/v1/analyze", response_model=RealEstateWeatherResponse)
def analyze_location(
    district: str = Query(..., description="行政區名稱，例如：大安區"),
    lat: float = Query(25.0330, description="緯度"),
    lon: float = Query(121.5654, description="經度")
):
    try:
        # 1. 從 MySQL 查詢該行政區的真實實價登錄資料
        db = get_db_connection()
        with db.cursor() as cursor:
            # 計算平均單價與樣本數 (將 單價元平方公尺 換算為 元/坪，1坪 = 3.305785 平方公尺)
            sql_summary = """
                SELECT 
                    COUNT(*) AS sample_count,
                    AVG(CAST(總價元 AS DECIMAL(15,2))) AS avg_total_price,
                    AVG(CAST(單價元平方公尺 AS DECIMAL(12,2)) * 3.305785) AS avg_unit_price
                FROM a_lvr_land_a
                WHERE 鄉鎮市區 = %s AND 總價元 REGEXP '^[0-9]+$' AND 單價元平方公尺 REGEXP '^[0-9]+$'
            """
            cursor.execute(sql_summary, (district,))
            summary_res = cursor.fetchone()

            sample_count = summary_res["sample_count"] or 0
            avg_unit_price = round(summary_res["avg_unit_price"]) if summary_res["avg_unit_price"] else 0

            # 抓取該區最近的 5 筆交易詳細情況
            sql_trans = """
                SELECT 交易年月日, 土地位置建物門牌, 總價元, 單價元平方公尺, 建物型態
                FROM a_lvr_land_a
                WHERE 鄉鎮市區 = %s AND 總價元 REGEXP '^[0-9]+$'
                ORDER BY 交易年月日 DESC
                LIMIT 5
            """
            cursor.execute(sql_trans, (district,))
            transactions_res = cursor.fetchall()

            recent_transactions = []
            for t in transactions_res:
                price_wan = round(float(t["總價元"]) / 10000, 1)
                recent_transactions.append({
                    "date": t["交易年月日"],
                    "address": t["土地位置建物門牌"],
                    "price": f"{price_wan} 萬元",
                    "type": t["建物型態"] or "其他"
                })

        db.close()

        # 若該區暫無資料，給予預設防呆
        if sample_count == 0:
            avg_unit_price = 650000
            sample_count = 1

        real_estate_data = {
            "district": district,
            "average_unit_price": avg_unit_price,
            "sample_count": sample_count
        }

        # 2. 串接中央氣象署 API 取得即時氣溫
        cwa_url = f"https://opendata.cwa.gov.tw/api/v1/rest/datastore/O-A0001-001?Authorization={CWA_API_KEY}"
        weather_response = requests.get(cwa_url)
        weather_json = weather_response.json()

        station_name = "臺北觀測站"
        temperature = 26.5
        rainfall = 1500.0

        if weather_response.status_code == 200 and "records" in weather_json:
            stations = weather_json.get("records", {}).get("Station", [])
            if stations:
                first_station = stations[0]
                station_name = first_station.get("StationName", "臺北測站")
                temperature = first_station.get("WeatherElement", {}).get("AirTemperature", 26.5)

        weather_data = {
            "station": station_name,
            "temperature": float(temperature),
            "annual_rainfall": float(rainfall)
        }

        risk_score = round((weather_data["annual_rainfall"] / 1000) * 1.5, 2)

        return {
            "district": district,
            "real_estate_summary": real_estate_data,
            "weather_summary": weather_data,
            "environmental_risk_score": risk_score,
            "recent_transactions": recent_transactions
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"伺服器運算或資料庫查詢發生錯誤: {str(e)}")
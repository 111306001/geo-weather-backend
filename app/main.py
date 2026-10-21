import os
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
import requests
from dotenv import load_dotenv

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

# 從環境變數中讀取氣象署 API Key
CWA_API_KEY = os.getenv("CWA_API_KEY")

@app.get("/")
def read_root():
    return {"message": "歡迎使用智慧不動產與氣象風險評估後端系統！請造訪 /docs 查看 API 文件。"}

@app.get("/api/v1/districts")
def get_districts():
    """提供全台縣市與鄉鎮市區對應資料供前端呼叫"""
    return TAIWAN_ADMIN_DISTRICTS

@app.get("/api/v1/analyze", response_model=RealEstateWeatherResponse)
def analyze_location(
    district: str = Query(..., description="行政區名稱，例如：大安區"),
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

        # 2. 模擬不動產實價登錄資料
        real_estate_data = {
            "district": district,
            "average_unit_price": 850000,
            "sample_count": 42
        }

        # 3. 計算環境風險分數
        risk_score = round((weather_data["annual_rainfall"] / 1000) * 1.5, 2)

        return {
            "district": district,
            "real_estate_summary": real_estate_data,
            "weather_summary": weather_data,
            "environmental_risk_score": risk_score
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"外部 API 串接或運算發生錯誤: {str(e)}")
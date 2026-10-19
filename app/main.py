from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
import requests

app = FastAPI(
    title="GeoWeather Real Estate Analytics Backend",
    description="整合不動產實價登錄與中央氣象署開放資料的雲端後端系統",
    version="1.0.0"
)

class RealEstateWeatherResponse(BaseModel):
    district: str
    real_estate_summary: dict
    weather_summary: dict
    environmental_risk_score: float

@app.get("/")
def read_root():
    return {"message": "歡迎使用智慧不動產與氣象風險評估後端系統！請造訪 /docs 查看 API 文件。"}

@app.get("/api/v1/analyze", response_model=RealEstateWeatherResponse)
def analyze_location(
    district: str = Query(..., description="行政區名稱，例如：大安區"),
    lat: float = Query(25.0330, description="緯度"),
    lon: float = Query(121.5654, description="經度")
):
    try:
        # 模擬不動產實價登錄資料
        real_estate_data = {
            "district": district,
            "average_unit_price": 850000,
            "sample_count": 42
        }

        # 模擬中央氣象署氣象資料
        weather_data = {
            "station": "台北觀測站",
            "temperature": 26.5,
            "annual_rainfall": 2050.2
        }

        # 簡單的跨域數據綜合風險計算
        risk_score = round((weather_data["annual_rainfall"] / 1000) * 1.5, 2)

        return {
            "district": district,
            "real_estate_summary": real_estate_data,
            "weather_summary": weather_data,
            "environmental_risk_score": risk_score
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"外部 API 串接或運算發生錯誤: {str(e)}")
    
    
# 🗺️ 智慧不動產與氣象 GIS 系統 (GeoWeather Real Estate Analytics System)

整合真實不動產實價登錄 MySQL 資料庫與中央氣象署（CWA）即時開放資料的地理資訊與不動產分析系統。本系統採用 FastAPI 作為雲端後端，並結合 Leaflet.js 地圖介面與現代化網頁儀表板，提供使用者視覺化的區域房價與環境風險評估。

---

## 🚀 系統功能特色

* **即時地理空間互動 (GIS Map)**：整合 OpenStreetMap 與 Leaflet.js，支援點擊地圖座標查詢或透過地址關鍵字搜尋特定路段。
* **實價登錄資料庫串接**：連接 MySQL 資料庫（`lvr_landcsv`），動態計算指定行政區的平均單價、樣本數，並提供近期詳細交易紀錄（包含總價、建物型態、交易日期與門牌）。
* **中央氣象署 API 串接**：即時取得觀測站氣溫與環境數據，並自動計算綜合環境風險分數。
* **響應式管理介面**：左側提供完整控制面板與數據儀表板，右側為全螢幕互動地圖，並支援詳細交易明細彈出視窗（Modal）。

---

## 🛠️ 專案技術堆疊

* **後端 (Backend)**：Python, FastAPI, Uvicorn, PyMySQL, Requests, Python-dotenv, Pydantic
* **前端 (Frontend)**：HTML5, CSS3, JavaScript (ES6+), Leaflet.js (地圖圖資)
* **資料庫 (Database)**：MySQL (內含實價登錄資料表 `a_lvr_land_a` 與 `a_lvr_land_a_build`)

---

## 📂 專案結構說明

```text
├── app/
│   └── model.py         # Pydantic 資料模型與全台行政區對應資料
├── frontend.py          # FastAPI 應用程式主程式（含 MySQL 資料庫連線與分析邏輯）
├── main.py              # 雲端後端系統主程式（輕量版本）
├── index.html           # 前端介面與 Leaflet.js 地圖互動邏輯
├── style.css            # 系統樣式與互動面板排版
├── lvr_landcsv.sql      # MySQL 資料庫傾印檔案（實價登錄與建物明細）
└── README.md            # 專案說明文件
```

---

## ⚙️ 安裝與執行步驟

### 1. 環境準備
請確保您的本機環境已安裝：
* Python 3.8 或以上版本
* MySQL / MariaDB 資料庫伺服器

### 2. 資料庫還原
將專案所附的 `lvr_landcsv.sql` 匯入至您的 MySQL 資料庫中，確保資料庫名稱為 `lvr_landcsv`，且資料表 `a_lvr_land_a` 存在。

### 3. 安裝 Python 依賴套件
在命令提示字元中執行以下指令安裝必要套件：
```bash
pip install fastapi uvicorn pymysql requests python-dotenv pydantic
```

### 4. 設定環境變數
在專案根目錄下建立 `.env` 檔案，並填入您的中央氣象署 API 金鑰：
```env
CWA_API_KEY=您的中央氣象署API_KEY
```

同時，請檢查 `frontend.py` 中的 `get_db_connection()` 函式，確認 MySQL 的使用者名稱與密碼是否與您的本機設定相符：
```python
def get_db_connection():
    return pymysql.connect(
        host="localhost",
        user="root",
        password="您的MySQL密碼",      
        database="lvr_landcsv",
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor
    )
```

### 5. 啟動後端伺服器
使用 Uvicorn 啟動 FastAPI 服務：
```bash
uvicorn frontend:app --reload
```
*(伺服器將運行於 `http://127.0.0.1:8000`)*

### 6. 開啟前端介面
直接使用瀏覽器開啟專案中的 `index.html` 檔案，或透過 Live Server 執行，即可開始操作智慧不動產與氣象 GIS 系統。

---

## 📄 API 文件
當後端伺服器啟動後，您可以造訪 [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) 查看由 FastAPI 自動產生的互動式 Swagger UI API 文件。
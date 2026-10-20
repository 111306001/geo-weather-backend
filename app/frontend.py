import streamlit as st
import requests
import folium
from streamlit_folium import st_folium

# 設定網頁標題與版面
st.set_page_config(
    page_title="智慧不動產與氣象地圖分析系統",
    page_icon="🗺️",
    layout="wide"
)

st.title("🗺️ 智慧不動產與氣象風險評估地圖系統")
st.markdown("點擊下方地圖的任意位置，或選擇特定行政區，即可即時查詢該區域的氣象環境與不動產行情分析。")

# 側邊欄：手動輸入或檢視當前選取座標
st.sidebar.header("📍 查詢控制台")
district_input = st.sidebar.text_input("行政區名稱", value="大安區")

# 預設台北車站中心座標
default_lat = 25.0478
default_lon = 121.5170

st.sidebar.markdown("---")
st.sidebar.info("💡 提示：您也可以直接點擊地圖上的任意位置來選定查詢點。")

# 建立 Folium 互動地圖 (以台北市為中心)
m = folium.Map(location=[default_lat, default_lon], zoom_start=13)

# 在地圖上加入點擊事件捕獲
# 使用 st_folium 渲染地圖並取得使用者互動資料
col_map, col_result = st.columns([1.2, 1])

with col_map:
    st.subheader("🌐 互動式 GIS 地圖")
    # 渲染地圖並取得點擊事件
    map_data = st_folium(m, width=700, height=500)

# 取得點擊後的經緯度（如果使用者有點擊地圖的話）
selected_lat = default_lat
selected_lon = default_lon

if map_data and map_data.get("last_clicked"):
    selected_lat = map_data["last_clicked"]["lat"]
    selected_lon = map_data["last_clicked"]["lng"]
    st.sidebar.success(f"已選擇地圖座標：\n緯度: {selected_lat:.4f}, 經度: {selected_lon:.4f}")

with col_result:
    st.subheader("📊 區域分析報告")
    
    # 查詢按鈕
    if st.button("🚀 開始分析選定區域", type="primary"):
        with st.spinner("正在向雲端後端與氣象/不動產 API 取得數據..."):
            try:
                # 呼叫 FastAPI 後端
                api_url = f"http://127.0.0.1:8000/api/v1/analyze?district={district_input}&lat={selected_lat}&lon={selected_lon}"
                response = requests.get(api_url)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    st.success(f"成功取得 【{data['district']}】 報告！")
                    
                    # 數據指標卡片
                    st.metric(
                        label="區域平均單價", 
                        value=f"{data['real_estate_summary']['average_unit_price']:,} 元/坪",
                        delta=f"樣本數: {data['real_estate_summary']['sample_count']}"
                    )
                    st.metric(
                        label="觀測站氣溫", 
                        value=f"{data['weather_summary']['temperature']} °C",
                        delta=data['weather_summary']['station']
                    )
                    st.metric(
                        label="環境風險計算分數", 
                        value=f"{data['environmental_risk_score']}",
                        delta="氣候綜合權重"
                    )
                    
                    with st.expander("🔍 檢視完整 JSON 原始資料"):
                        st.json(data)
                        
                else:
                    st.error(f"後端回應錯誤 ({response.status_code})：{response.text}")
                    
            except requests.exceptions.ConnectionError:
                st.error("無法連線至後端伺服器！請確認 FastAPI 是否已正常啟動。")
            except Exception as e:
                st.error(f"發生未預期的錯誤：{str(e)}")
    else:
        st.info("👈 請在地圖上點擊欲查詢的位置，或在左側輸入行政區後，點擊「開始分析選定區域」。")
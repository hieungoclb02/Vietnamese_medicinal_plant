import streamlit as st
st.set_page_config(page_title="Bản đồ Cây Thuốc", layout="centered")

import pandas as pd
import folium
import json
from folium.plugins import HeatMap
from streamlit_folium import st_folium

# ======================
# 1. Load dữ liệu có cache
# ======================
@st.cache_data
def load_data():
    df = pd.read_csv('clean.csv').fillna('')
    df = df[df['Phân bố'] != 0]
    return df

@st.cache_data
def load_city_data():
    city = pd.read_csv('vietnam_provinces.csv')
    return city.set_index('Tỉnh Thành')[['Latitude', 'Longitude']].to_dict('index')

@st.cache_data
def load_geojson():
    with open("vn.json", "r", encoding="utf-8") as f:
        return json.load(f)

@st.cache_data
def preprocess_plants(df, city_coords):
    plants = {province: {'lat': coord['Latitude'], 'lon': coord['Longitude'], 'medicinal plant': []}
              for province, coord in city_coords.items()}

    for _, row in df.iterrows():
        for province in plants:
            if province in row['Phân bố']:
                plants[province]['medicinal plant'].append(row['Tên khoa học'])
    return plants

# ======================
# 2. Tải dữ liệu
# ======================
df = load_data()
city_coords = load_city_data()
countries_geo = load_geojson()
plants = preprocess_plants(df, city_coords)

# ======================
# 3. Hàm hỗ trợ vẽ bản đồ và heatmap
# ======================
def draw_vietnam_map():
    m = folium.Map(location=[16.0, 108.0], zoom_start=6)
    vietnam_geo = next((f for f in countries_geo['features'] if f['properties']['name'] == 'Vietnam'), None)
    if vietnam_geo:
        folium.GeoJson(
            vietnam_geo,
            style_function=lambda x: {
                'fillColor': 'none',
                'color': 'red',
                'weight': 2,
                'fillOpacity': 0
            }
        ).add_to(m)
    return m

def create_heatmap(data_points):
    m = draw_vietnam_map()
    if data_points:
        HeatMap(data_points, radius=20, blur=15, max_zoom=10).add_to(m)
    return m

# ======================
# 4. Hàm xử lý tìm kiếm
# ======================
def find_by_disease(disease_name):
    related_plants = df[df['Công dụng'].str.contains(disease_name, case=False, na=False)]['Tên khoa học'].tolist()
    heat_data = [
        [info['lat'], info['lon'], sum(p in related_plants for p in info['medicinal plant'])]
        for info in plants.values()
        if any(p in related_plants for p in info['medicinal plant'])
    ]
    return create_heatmap(heat_data)

def find_by_ho(ho_):
    related_plants = df[df['Họ thực vật'].str.contains(ho_, case=False, na=False)]['Tên khoa học'].tolist()
    heat_data = [
        [info['lat'], info['lon'], sum(p in related_plants for p in info['medicinal plant'])]
        for info in plants.values()
        if any(p in related_plants for p in info['medicinal plant'])
    ]
    return create_heatmap(heat_data)

def find_by_plant(plant_name):
    related_plants = df[
        df['Tên tiếng Việt'].str.contains(plant_name, case=False, na=False) |
        df['Tên khoa học'].str.contains(plant_name, case=False, na=False) |
        df['Tên đồng nghĩa'].str.contains(plant_name, case=False, na=False)
    ]['Tên khoa học'].tolist()

    heat_data = [
        [info['lat'], info['lon'], sum(p in related_plants for p in info['medicinal plant'])]
        for info in plants.values()
        if any(p in related_plants for p in info['medicinal plant'])
    ]
    return create_heatmap(heat_data)

# ======================
# 5. Giao diện Streamlit
# ======================
# st.set_page_config(page_title="Bản đồ Cây Thuốc", layout="centered")
st.title("Bản đồ Dược liệu Việt Nam")
st.sidebar.header("🔎 Tìm kiếm thông tin")

option = st.sidebar.selectbox(
    "Chọn phương thức tìm kiếm:",
    ("Tìm kiếm theo Bệnh", "Tìm kiếm theo Cây Thuốc",'Tìm kiếm theo Họ')
)

if option == "Tìm kiếm theo Bệnh":
    disease_name = st.text_input("Nhập tên bệnh:")
    if disease_name:
        st_folium(find_by_disease(disease_name), width=700, height=500)

elif option == "Tìm kiếm theo Cây Thuốc":
    plant_name = st.text_input("Nhập tên cây thuốc:")
    if plant_name:
        st_folium(find_by_plant(plant_name), width=700, height=500)
elif option =='Tìm kiếm theo Họ':
    ho_ =st.text_input('Nhập tên Họ: ')
    if ho_:
        st_folium(find_by_ho(ho_),width=700, height=500)


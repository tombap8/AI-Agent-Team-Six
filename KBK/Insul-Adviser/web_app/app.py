import os
import json
import time
import math
import random
import datetime
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from PIL import Image

# Import the LibreLinkUp client
from libre_client import LibreLinkUpClient

# ----------------------------------------------------
# 1. Page Configuration & Custom Theme Styling
# ----------------------------------------------------
st.set_page_config(
    page_title="Insulin Dose Advisor",
    page_icon="🩺",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Custom Slate Dark Theme CSS Injection
st.markdown("""
<style>
    /* Global Background and Text Color */
    .stApp {
        background-color: #0F172A;
        color: #F8FAFC;
    }
    
    /* Top Header Background */
    [data-testid="stHeader"] {
        background-color: rgba(15, 23, 42, 0.9) !important;
    }
    
    /* Modify default tabs header color */
    div.stTabs [data-baseweb="tab-list"] {
        background-color: #0F172A;
        border-bottom: 2px solid #334155;
        padding-bottom: 2px;
    }
    div.stTabs [data-baseweb="tab"] {
        color: #94A3B8;
        font-weight: 700;
        padding: 10px 20px;
    }
    div.stTabs [aria-selected="true"] {
        color: #2DD4BF !important;
        border-bottom-color: #0D9488 !important;
    }
    
    /* Style container blocks to look like compose Cards */
    div[data-testid="stVerticalBlock"] > div[style*="border"] {
        background-color: #1E293B !important;
        border: 1px solid #334155 !important;
        border-radius: 20px !important;
        padding: 20px !important;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -2px rgba(0, 0, 0, 0.1) !important;
    }

    /* Style primary buttons */
    div.stButton > button[kind="primary"] {
        background-color: #0D9488 !important;
        color: #F8FAFC !important;
        border: none !important;
        border-radius: 12px !important;
        font-weight: 700 !important;
        width: 100% !important;
        padding: 10px 24px !important;
        transition: all 0.2s ease !important;
    }
    div.stButton > button[kind="primary"]:hover {
        background-color: #14B8A6 !important;
        box-shadow: 0 0 12px rgba(45, 212, 191, 0.4) !important;
    }

    /* Secondary buttons */
    div.stButton > button[kind="secondary"] {
        background-color: #1E293B !important;
        color: #F8FAFC !important;
        border: 1px solid #334155 !important;
        border-radius: 12px !important;
        width: 100% !important;
    }
    div.stButton > button[kind="secondary"]:hover {
        border-color: #94A3B8 !important;
    }

    /* Custom Input fields labels color */
    label[data-testid="stWidgetLabel"] {
        color: #94A3B8 !important;
        font-weight: 500 !important;
    }

    /* Custom horizontal divider */
    hr {
        border: 0;
        border-top: 1px solid #334155;
        margin: 1.5rem 0;
    }

    /* Target notification style */
    .target-info {
        background-color: rgba(13, 148, 136, 0.05);
        border: 1px solid rgba(45, 212, 191, 0.15);
        border-radius: 12px;
        padding: 12px;
        font-size: 12px;
        color: #94A3B8;
        line-height: 1.5;
        margin-top: 10px;
    }
</style>
""", unsafe_allow_html=True)

# ----------------------------------------------------
# 2. Data Directories & File Persistence Constants
# ----------------------------------------------------
DATA_DIR = "data"
PHOTOS_DIR = os.path.join(DATA_DIR, "photos")
SETTINGS_FILE = os.path.join(DATA_DIR, "settings.json")
LOGS_FILE = os.path.join(DATA_DIR, "logs.csv")
GLUCOSE_FILE = os.path.join(DATA_DIR, "libre_glucose.csv")

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(PHOTOS_DIR, exist_ok=True)

DEFAULT_SETTINGS = {
    "targetGlucose": 120,
    "icr": 10.0,
    "isf": 50.0,
    "roundingMode": "0.5",  # "NONE", "0.5", "1.0"
    "walking30Reduction": 0.15,
    "walking60Reduction": 0.25,
    "running30Reduction": 0.35,
    "running60Reduction": 0.50,
    "libreEmail": "",
    "librePassword": "",
    "libreRegion": "ap",
    "libreConnected": False,
    "libreLastSyncTime": 0,
    "libreHbA1c": 7.6,
    "libreAvgGlucose": 176.0
}

FOODS_DATABASE = [
    {"name": "흰쌀밥", "category": "밥류", "carbs": 65.0, "unitDescription": "1공기 (210g)"},
    {"name": "현미밥", "category": "밥류", "carbs": 55.0, "unitDescription": "1공기 (210g)"},
    {"name": "잡곡밥", "category": "밥류", "carbs": 58.0, "unitDescription": "1공기 (210g)"},
    {"name": "라면", "category": "면류", "carbs": 80.0, "unitDescription": "1봉지"},
    {"name": "식빵", "category": "빵류", "carbs": 15.0, "unitDescription": "1장"},
    {"name": "피자", "category": "간식류", "carbs": 30.0, "unitDescription": "1조각"},
    {"name": "짜장면", "category": "면류", "carbs": 120.0, "unitDescription": "1그릇"},
    {"name": "떡볶이", "category": "간식류", "carbs": 80.0, "unitDescription": "1인분"},
    {"name": "바나나", "category": "과일류", "carbs": 25.0, "unitDescription": "1개"},
    {"name": "사과", "category": "과일류", "carbs": 20.0, "unitDescription": "1개 (중)"},
    {"name": "귤", "category": "과일류", "carbs": 10.0, "unitDescription": "1개"},
    {"name": "콜라", "category": "음료류", "carbs": 27.0, "unitDescription": "1캔 (250ml)"},
    {"name": "우유", "category": "음료류", "carbs": 12.0, "unitDescription": "1컵 (200ml)"},
    {"name": "고구마", "category": "구황작물", "carbs": 30.0, "unitDescription": "1개 (중, 120g)"},
    {"name": "감자", "category": "구황작물", "carbs": 20.0, "unitDescription": "1개 (중, 130g)"},
    {"name": "삶은 계란", "category": "단백질", "carbs": 1.0, "unitDescription": "1개"},
    {"name": "닭가슴살", "category": "단백질", "carbs": 0.0, "unitDescription": "1팩 (100g)"},
    {"name": "사과 주스", "category": "음료류", "carbs": 30.0, "unitDescription": "1컵 (200ml)"}
]

# ----------------------------------------------------
# 3. Helper Functions for Data Access
# ----------------------------------------------------
def load_settings():
    if not os.path.exists(SETTINGS_FILE):
        save_settings(DEFAULT_SETTINGS)
        return DEFAULT_SETTINGS
    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            # Fill missing keys in case of schema update
            for k, v in DEFAULT_SETTINGS.items():
                if k not in data:
                    data[k] = v
            return data
    except Exception:
        return DEFAULT_SETTINGS

def save_settings(settings):
    try:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=4, ensure_ascii=False)
    except Exception as e:
        st.error(f"설정 저장 중 오류: {str(e)}")

def load_logs():
    if not os.path.exists(LOGS_FILE):
        return []
    try:
        df = pd.read_csv(LOGS_FILE)
        # Convert timestamp to int/float
        df['timestamp'] = df['timestamp'].astype(float)
        # Fill missing string photo cols
        if 'photoBefore' not in df.columns:
            df['photoBefore'] = ""
        if 'photoAfter' not in df.columns:
            df['photoAfter'] = ""
        # Return as list of dicts, sorted newest first
        records = df.to_dict('records')
        records.sort(key=lambda x: x['timestamp'], reverse=True)
        return records
    except Exception:
        return []

def add_log(log_entry):
    records = load_logs()
    records.append(log_entry)
    df = pd.DataFrame(records)
    df.to_csv(LOGS_FILE, index=False)

def clear_logs():
    if os.path.exists(LOGS_FILE):
        os.remove(LOGS_FILE)
    # Clean photos directory contents as well
    for filename in os.listdir(PHOTOS_DIR):
        file_path = os.path.join(PHOTOS_DIR, filename)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
        except Exception:
            pass

def update_log_after_photo(timestamp, photo_path):
    records = load_logs()
    for rec in records:
        if float(rec['timestamp']) == float(timestamp):
            rec['photoAfter'] = photo_path
            break
    df = pd.DataFrame(records)
    df.to_csv(LOGS_FILE, index=False)

def load_glucose():
    if not os.path.exists(GLUCOSE_FILE):
        return []
    try:
        readings = []
        with open(GLUCOSE_FILE, "r", encoding="utf-8") as f:
            for line in f:
                parts = line.strip().split(",")
                if len(parts) == 2:
                    readings.append((float(parts[0]), int(parts[1])))
        return readings
    except Exception:
        return []

def save_glucose(readings):
    try:
        with open(GLUCOSE_FILE, "w", encoding="utf-8") as f:
            for ts, val in readings:
                f.write(f"{ts},{val}\n")
    except Exception:
        pass

def generate_mock_libre_data():
    readings = []
    now = time.time() * 1000.0
    fifteen_minutes = 15 * 60 * 1000.0
    total_points = 4 * 24 * 7  # 672 points
    
    for i in range(total_points):
        t = now - (total_points - i) * fifteen_minutes
        base = 145.0
        diurnal = 25.0 * math.sin(2.0 * math.pi * (i % 96) / 96.0)
        noise = (random.random() - 0.5) * 15.0
        
        day_hour_index = i % 96
        meal_spike = 0.0
        if 32 <= day_hour_index <= 44:
            meal_spike = 40.0 * math.sin(math.pi * (day_hour_index - 32) / 12.0)
        elif 52 <= day_hour_index <= 66:
            meal_spike = 55.0 * math.sin(math.pi * (day_hour_index - 52) / 14.0)
        elif 76 <= day_hour_index <= 92:
            meal_spike = 65.0 * math.sin(math.pi * (day_hour_index - 76) / 16.0)
            
        glucose = int(base + diurnal + noise + meal_spike)
        glucose = max(50, min(320, glucose))
        readings.append((t, glucose))
    
    save_glucose(readings)
    return readings

def save_uploaded_file(uploaded_file, prefix="photo"):
    if uploaded_file is None:
        return ""
    file_ext = os.path.splitext(uploaded_file.name)[1]
    if not file_ext:
        file_ext = ".jpg"
    filename = f"{prefix}_{int(time.time() * 1000)}{file_ext}"
    filepath = os.path.join(PHOTOS_DIR, filename)
    with open(filepath, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return os.path.join("data", "photos", filename).replace("\\", "/")

# ----------------------------------------------------
# 4. Initialize Session State Variables
# ----------------------------------------------------
# Check cached settings
settings = load_settings()

if "settings" not in st.session_state:
    st.session_state.settings = settings

# Navigation state
if "active_tab" not in st.session_state:
    st.session_state.active_tab = 0

# Sync status
if "is_syncing" not in st.session_state:
    st.session_state.is_syncing = False
if "sync_error" not in st.session_state:
    st.session_state.sync_error = None

# Cart / Meal Builder temporary state
if "meal_cart" not in st.session_state:
    st.session_state.meal_cart = {}

# Calculator Input buffers
if "input_carbs" not in st.session_state:
    st.session_state.input_carbs = ""

# Glucose readings
readings = load_glucose()
if not readings:
    readings = generate_mock_libre_data()

# ----------------------------------------------------
# 5. Render Navigation Bar
# ----------------------------------------------------
st.title("Insulin Dose Advisor")

nav_cols = st.columns(4)
nav_buttons = [
    ("🩺 계산기", 0),
    ("🥗 식단사전", 1),
    ("📋 투약기록", 2),
    ("⚙️ 환경설정", 3)
]

for idx, (label, tab_val) in enumerate(nav_buttons):
    with nav_cols[idx]:
        is_active = (st.session_state.active_tab == tab_val)
        if st.button(
            label, 
            key=f"nav_btn_{tab_val}", 
            use_container_width=True,
            type="primary" if is_active else "secondary"
        ):
            st.session_state.active_tab = tab_val
            st.rerun()

st.markdown("<hr/>", unsafe_allow_html=True)

# Fetch latest configurations
cur_settings = st.session_state.settings

# ----------------------------------------------------
# TAB 0: ADVISOR SCREEN (🩺 계산기)
# ----------------------------------------------------
if st.session_state.active_tab == 0:
    
    # 1. Glycemic Header Card
    with st.container(border=True):
        col_header, col_action = st.columns([3, 1])
        with col_header:
            st.markdown(f"### 나의 당뇨 상태 요약")
            is_connected = cur_settings.get("libreConnected", False)
            status_color = "#10B981" if is_connected else "#64748B"
            status_text = "LibreView 연동됨" if is_connected else "데모 모드 (가상 데이터)"
            st.markdown(f"<span style='color:{status_color}; font-weight:bold; font-size:12px;'>{status_text}</span>", unsafe_allow_html=True)
        
        with col_action:
            if st.button("🔄 새로고침", key="sync_recent_bg", use_container_width=True):
                email = cur_settings.get("libreEmail", "")
                password = cur_settings.get("librePassword", "")
                region = cur_settings.get("libreRegion", "ap")
                
                if not email or not password:
                    st.session_state.sync_error = "이메일과 비밀번호를 설정 화면에 입력해 주세요."
                else:
                    st.session_state.is_syncing = True
                    st.session_state.sync_error = None
                    
                    client = LibreLinkUpClient()
                    res = client.fetch_recent_glucose(email, password, region)
                    
                    st.session_state.is_syncing = False
                    if res.get("success"):
                        save_glucose(res.get("readings", []))
                        cur_settings["libreConnected"] = True
                        cur_settings["libreLastSyncTime"] = int(time.time() * 1000)
                        cur_settings["libreHbA1c"] = float(res.get("est_hba1c", 7.6))
                        cur_settings["libreAvgGlucose"] = float(res.get("avg_glucose", 176.0))
                        save_settings(cur_settings)
                        st.session_state.settings = cur_settings
                        st.toast("LibreView 데이터 동기화 완료!", icon="✅")
                        st.rerun()
                    else:
                        st.session_state.sync_error = res.get("message")
            
        if st.session_state.sync_error:
            st.error(f"❌ {st.session_state.sync_error}")

        st.markdown("<hr style='margin: 0.5rem 0;'/>", unsafe_allow_html=True)
        
        # Core HbA1c & Avg BG Stats
        stat_cols = st.columns(2)
        with stat_cols[0]:
            hba1c_val = cur_settings.get("libreHbA1c", 7.6)
            st.markdown(f"<div style='text-align:center;'><span style='color:#94A3B8; font-size:12px;'>당화혈색소 추정치</span><br/><strong style='color:#F8FAFC; font-size:24px;'>{hba1c_val:.1f} %</strong></div>", unsafe_allow_html=True)
        with stat_cols[1]:
            avg_bg_val = cur_settings.get("libreAvgGlucose", 176.0)
            st.markdown(f"<div style='text-align:center;'><span style='color:#94A3B8; font-size:12px;'>일주일 평균 혈당</span><br/><strong style='color:#F8FAFC; font-size:24px;'>{int(avg_bg_val)} mg/dL</strong></div>", unsafe_allow_html=True)
            
        st.markdown("<br/>", unsafe_allow_html=True)
        st.markdown("<span style='font-size:13px; font-weight:bold; color:#F8FAFC;'>최근 일주일 혈당 변화 추이</span>", unsafe_allow_html=True)
        
        # Build Line Chart
        readings = load_glucose()
        if not readings:
            readings = generate_mock_libre_data()
            
        # Draw interactive line chart using Plotly
        df_chart = pd.DataFrame(readings, columns=["Timestamp", "Glucose"])
        df_chart["Time"] = pd.to_datetime(df_chart["Timestamp"], unit="ms")
        
        fig = go.Figure()
        # Area fill
        fig.add_trace(go.Scatter(
            x=df_chart["Time"], y=df_chart["Glucose"],
            fill='tozeroy',
            fillcolor='rgba(13, 148, 136, 0.1)',
            line=dict(color='#2DD4BF', width=3.5),
            name="혈당 수치"
        ))
        # High limit limit lines (180 mg/dL)
        fig.add_hline(y=180, line_dash="dash", line_color="#EF4444", line_width=1.5, annotation_text="고혈당 기준 (180)", annotation_position="top left", annotation_font_color="#EF4444")
        # Low limit lines (70 mg/dL)
        fig.add_hline(y=70, line_dash="dash", line_color="#3B82F6", line_width=1.5, annotation_text="저혈당 기준 (70)", annotation_position="bottom left", annotation_font_color="#3B82F6")
        # Target limit line (120 mg/dL)
        fig.add_hline(y=120, line_color="rgba(45, 212, 191, 0.2)", line_width=1)
        
        fig.update_layout(
            paper_bgcolor="#0F172A",
            plot_bgcolor="#0F172A",
            margin=dict(l=25, r=10, t=10, b=25),
            height=180,
            xaxis=dict(showgrid=False, color="#64748B"),
            yaxis=dict(
                range=[40, 310],
                showgrid=True,
                gridcolor="#334155",
                color="#64748B",
                tickvals=[40, 70, 120, 180, 300]
            ),
            showlegend=False
        )
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

    # 2. Insulin Calculation Card
    with st.container(border=True):
        st.markdown("### 속효성 인슐린 주사 계산기")
        
        # Pre-meal Blood Glucose Input
        bg_input = st.text_input("식전 현재 혈당 (mg/dL)", value="", placeholder="예: 145")
        
        # Compute status tag based on input
        bg_val = None
        glucose_status_html = ""
        if bg_input.strip().isdigit():
            bg_val = int(bg_input.strip())
            if bg_val < 70:
                glucose_status_html = "<span style='color:#3B82F6; font-weight:bold;'>저혈당 경보</span>"
            elif bg_val <= 140:
                glucose_status_html = "<span style='color:#10B981; font-weight:bold;'>정상 혈당 범위</span>"
            elif bg_val <= 180:
                glucose_status_html = "<span style='color:#F59E0B; font-weight:bold;'>조금 높은 혈당</span>"
            else:
                glucose_status_html = "<span style='color:#EF4444; font-weight:bold;'>고혈당 경보</span>"
        else:
            glucose_status_html = "<span style='color:#94A3B8;'>혈당을 입력하세요</span>"
            
        st.markdown(f"<div style='text-align: right; margin-top: -15px; margin-bottom: 10px; font-size:12px;'>상태: {glucose_status_html}</div>", unsafe_allow_html=True)
        
        # Carbohydrates Input
        carbs_placeholder = "0"
        if st.session_state.input_carbs:
            carbs_placeholder = st.session_state.input_carbs
        carbs_input = st.text_input("식사 탄수화물량 (g)", value=st.session_state.input_carbs, placeholder="예: 65")
        carbs_val = 0.0
        if carbs_input.strip():
            try:
                carbs_val = float(carbs_input.strip())
            except ValueError:
                pass
                
        # Post-meal exercise selection dropdown
        ex_walk30 = int(cur_settings.get("walking30Reduction", 0.15) * 100)
        ex_walk60 = int(cur_settings.get("walking60Reduction", 0.25) * 100)
        ex_run30 = int(cur_settings.get("running30Reduction", 0.35) * 100)
        ex_run60 = int(cur_settings.get("running60Reduction", 0.50) * 100)
        
        exercise_options = [
            f"운동 계획 없음 (0% 감량)",
            f"식후 30분 걷기 ({ex_walk30}% 감량)",
            f"식후 1시간 걷기 ({ex_walk60}% 감량)",
            f"식후 30분 달리기 ({ex_run30}% 감량)",
            f"식후 1시간 달리기 ({ex_run60}% 감량)"
        ]
        
        selected_exercise = st.selectbox("식후 예정 운동", options=exercise_options, index=0)
        
        # Map selected exercise to reduction rate
        reduction_rate = 0.0
        ex_duration = 0
        ex_name = "없음"
        
        if "30분 걷기" in selected_exercise:
            reduction_rate = cur_settings.get("walking30Reduction", 0.15)
            ex_duration = 30
            ex_name = "걷기 30분"
        elif "1시간 걷기" in selected_exercise:
            reduction_rate = cur_settings.get("walking60Reduction", 0.25)
            ex_duration = 60
            ex_name = "걷기 1시간"
        elif "30분 달리기" in selected_exercise:
            reduction_rate = cur_settings.get("running30Reduction", 0.35)
            ex_duration = 30
            ex_name = "달리기 30분"
        elif "1시간 달리기" in selected_exercise:
            reduction_rate = cur_settings.get("running60Reduction", 0.50)
            ex_duration = 60
            ex_name = "달리기 1시간"

        # Meal Photo Attachment (Before eating)
        st.markdown("<span style='font-size:13px; font-weight:medium; color:#94A3B8;'>식사 전 음식 사진 첨부</span>", unsafe_allow_html=True)
        photo_before_file = st.file_uploader("음식 사진 등록 (선택)", type=["png", "jpg", "jpeg"], key="photo_before_uploader")
        
        if photo_before_file:
            st.image(photo_before_file, caption="식사 전 음식 사진", width=300)

    # 3. Calculation Result Card
    if bg_val is not None or carbs_val > 0.0:
        with st.container(border=True):
            st.markdown("### 실시간 용량 계산서")
            
            icr = cur_settings.get("icr", 10.0)
            isf = cur_settings.get("isf", 50.0)
            target_glucose = cur_settings.get("targetGlucose", 120)
            rounding_mode = cur_settings.get("roundingMode", "0.5")
            
            # Dose components calculation
            food_dose = carbs_val / icr if icr > 0 else 0.0
            
            correction_dose = 0.0
            if bg_val is not None and isf > 0:
                correction_dose = (bg_val - target_glucose) / isf
                
            pre_exercise_total = food_dose + correction_dose
            exercise_reduction = 0.0
            if pre_exercise_total > 0:
                exercise_reduction = pre_exercise_total * reduction_rate
                
            raw_final_dose = pre_exercise_total - exercise_reduction
            if raw_final_dose < 0.0:
                raw_final_dose = 0.0
                
            # Rounding logic
            if rounding_mode == "0.5":
                final_dose = round(raw_final_dose * 2.0) / 2.0
            elif rounding_mode == "1.0":
                final_dose = float(round(raw_final_dose))
            else:
                final_dose = raw_final_dose # NONE
                
            # Breakdown display
            col_lbl, col_val = st.columns([3, 1])
            with col_lbl:
                st.markdown(f"식사용 용량 ({int(carbs_val)}g / ICR {int(icr)}g)")
            with col_val:
                st.markdown(f"<p style='text-align:right; font-weight:bold;'>+ {food_dose:.2f} U</p>", unsafe_allow_html=True)
                
            col_lbl2, col_val2 = st.columns([3, 1])
            with col_lbl2:
                bg_diff = bg_val - target_glucose if bg_val is not None else 0
                st.markdown(f"혈당 교정 용량 (차이 {bg_diff}mg / CF {int(isf)})")
            with col_val2:
                sign = "+" if correction_dose >= 0 else ""
                corr_color = "#F8FAFC" if correction_dose >= 0 else "#3B82F6"
                st.markdown(f"<p style='text-align:right; font-weight:bold; color:{corr_color};'>{sign} {correction_dose:.2f} U</p>", unsafe_allow_html=True)
                
            if reduction_rate > 0:
                col_lbl3, col_val3 = st.columns([3, 1])
                with col_lbl3:
                    st.markdown(f"식후 운동 감량 ({int(reduction_rate * 100)}% 감축)")
                with col_val3:
                    st.markdown(f"<p style='text-align:right; font-weight:bold; color:#F59E0B;'>- {exercise_reduction:.2f} U</p>", unsafe_allow_html=True)
                    
            st.markdown("<hr style='margin: 0.75rem 0;'/>", unsafe_allow_html=True)
            
            # Circular grand display
            circle_html = f"""
            <div style="display: flex; justify-content: center; align-items: center; margin: 15px 0;">
                <div style="
                    width: 160px;
                    height: 160px;
                    border-radius: 50%;
                    background: #0F172A;
                    padding: 4px;
                    background-image: linear-gradient(135deg, #0D9488, #F59E0B);
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    box-shadow: 0 8px 32px 0 rgba(13, 148, 136, 0.25);
                ">
                    <div style="
                        width: 100%;
                        height: 100%;
                        border-radius: 50%;
                        background: #1E293B;
                        display: flex;
                        flex-direction: column;
                        justify-content: center;
                        align-items: center;
                    ">
                        <span style="color: #94A3B8; font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;">권장 투여량</span>
                        <span style="color: #FBBF24; font-size: 36px; font-weight: 800; margin: 2px 0;">{final_dose:.1f} U</span>
                        {"<span style='color: #64748B; font-size: 10px;'>원합계: " + f"{raw_final_dose:.2f}" + " U</span>" if rounding_mode != "NONE" else ""}
                    </div>
                </div>
            </div>
            """
            st.markdown(circle_html, unsafe_allow_html=True)
            
            # Target range details
            st.markdown(f"""
            <div class="target-info">
                ℹ️ 목표 혈당 {target_glucose} mg/dL을 기준하고 있으며, 반올림 옵션은 {rounding_mode} 단위로 적용 중입니다.
            </div>
            """, unsafe_allow_html=True)
            
            # Save button
            if st.button("기록 저장 및 투약 완료", type="primary", key="save_insul_btn"):
                if bg_val is None:
                    st.error("현재 혈당을 올바르게 입력해야 저장할 수 있습니다.")
                else:
                    # Save image before eating if uploaded
                    photo_before_path = ""
                    if photo_before_file:
                        photo_before_path = save_uploaded_file(photo_before_file, "before")
                    
                    log = {
                        "timestamp": time.time() * 1000.0,
                        "currentGlucose": bg_val,
                        "carbs": carbs_val,
                        "exerciseName": ex_name,
                        "exerciseDuration": ex_duration,
                        "foodDose": food_dose,
                        "correctionDose": correction_dose,
                        "exerciseReduction": exercise_reduction,
                        "finalDose": final_dose,
                        "photoBefore": photo_before_path,
                        "photoAfter": ""
                    }
                    add_log(log)
                    st.session_state.input_carbs = ""  # Clear carb buffer
                    st.toast(f"속효성 인슐린 {final_dose}U 투여 및 로그 완료!", icon="💉")
                    time.sleep(1)
                    st.rerun()

# ----------------------------------------------------
# TAB 1: NUTRITION SCREEN (🥗 식단사전)
# ----------------------------------------------------
elif st.session_state.active_tab == 1:
    sub_tab_names = ["식사 탄수화물 사전", "권장 탄수화물 계산기"]
    sub_tab = st.radio("서브 메뉴 선택", sub_tab_names, index=0, horizontal=True, label_visibility="collapsed")
    
    # --- SUB TAB 1: Food Dictionary & Cart Builder ---
    if sub_tab == "식사 탄수화물 사전":
        # Meal Builder / Cart
        with st.container(border=True):
            st.markdown("### 임시 식사 담기 (Meal Builder)")
            
            cart = st.session_state.meal_cart
            if not cart:
                st.markdown("<p style='color:#64748B; text-align:center;'>사전에서 음식을 검색하여 식단을 완성하세요.</p>", unsafe_allow_html=True)
            else:
                total_carbs = 0.0
                for food_name, qty in list(cart.items()):
                    # Find food item carbs
                    food_ref = next((f for f in FOODS_DATABASE if f['name'] == food_name), None)
                    if food_ref:
                        item_carbs = food_ref['carbs'] * qty
                        total_carbs += item_carbs
                        
                        col_food_desc, col_qty_actions = st.columns([3, 1.5])
                        with col_food_desc:
                            st.markdown(f"**{food_name}**")
                            st.markdown(f"<span style='color:#94A3B8; font-size:11px;'>단당 {int(food_ref['carbs'])}g x {qty}개</span>", unsafe_allow_html=True)
                        with col_qty_actions:
                            q_cols = st.columns(3)
                            with q_cols[0]:
                                if st.button("➖", key=f"sub_{food_name}", size="small", use_container_width=True):
                                    if qty > 1:
                                        cart[food_name] -= 1
                                    else:
                                        del cart[food_name]
                                    st.session_state.meal_cart = cart
                                    st.rerun()
                            with q_cols[1]:
                                st.markdown(f"<p style='text-align:center; font-weight:bold; margin-top:5px;'>{qty}</p>", unsafe_allow_html=True)
                            with q_cols[2]:
                                if st.button("➕", key=f"add_qty_{food_name}", size="small", use_container_width=True):
                                    cart[food_name] += 1
                                    st.session_state.meal_cart = cart
                                    st.rerun()
                
                st.markdown("<hr style='margin:0.5rem 0;'/>", unsafe_allow_html=True)
                col_tot_lbl, col_tot_val = st.columns(2)
                with col_tot_lbl:
                    st.markdown("**총 탄수화물 합계**")
                with col_tot_val:
                    st.markdown(f"<p style='text-align:right; font-size:20px; font-weight:800; color:#F59E0B;'>{int(total_carbs)} g</p>", unsafe_allow_html=True)
                    
                col_clear, col_send = st.columns(2)
                with col_clear:
                    if st.button("식단 초기화", key="clear_cart_btn", use_container_width=True):
                        st.session_state.meal_cart = {}
                        st.rerun()
                with col_send:
                    if st.button("계산기로 전송", type="primary", key="send_cart_btn", use_container_width=True):
                        st.session_state.input_carbs = str(int(total_carbs))
                        st.session_state.active_tab = 0  # Navigate back to advisor
                        st.toast("총 탄수화물량이 계산기에 입력되었습니다!", icon="🥗")
                        time.sleep(1)
                        st.rerun()
                        
        # Search & List Food database
        search_query = st.text_input("🔍 음식명 또는 카테고리 검색", value="", placeholder="예: 밥, 바나나, 라면")
        
        filtered_foods = FOODS_DATABASE
        if search_query.strip():
            filtered_foods = [
                f for f in FOODS_DATABASE 
                if search_query.lower() in f['name'].lower() or search_query.lower() in f['category'].lower()
            ]
            
        st.markdown("<span style='font-size:12px; font-weight:medium; color:#94A3B8;'>자주 찾는 한국인 탄수화물 사전</span>", unsafe_allow_html=True)
        
        for food in filtered_foods:
            with st.container(border=True):
                col_item_desc, col_item_action = st.columns([3, 1.2])
                with col_item_desc:
                    st.markdown(f"**{food['name']}** <span style='font-size:10px; background-color:#334155; padding:2px 6px; border-radius:4px; color:#64748B; margin-left:6px;'>{food['category']}</span>", unsafe_allow_html=True)
                    st.markdown(f"<span style='color:#94A3B8; font-size:12px;'>기준량: {food['unitDescription']}</span>", unsafe_allow_html=True)
                with col_item_action:
                    st.markdown(f"<p style='text-align:right; font-size:16px; font-weight:bold; color:#FBBF24; margin-bottom:5px;'>{int(food['carbs'])}g</p>", unsafe_allow_html=True)
                    if st.button("➕ 담기", key=f"cart_add_{food['name']}", use_container_width=True):
                        cart = st.session_state.meal_cart
                        cart[food['name']] = cart.get(food['name'], 0) + 1
                        st.session_state.meal_cart = cart
                        st.toast(f"{food['name']} 식단에 추가됨", icon="🛒")
                        st.rerun()

    # --- SUB TAB 2: TDEE Daily Carbs Calculator ---
    else:
        with st.container(border=True):
            st.markdown("### 일일 에너지 소비량 & 탄수화물 계산기")
            
            gender = st.radio("성별", ["남성", "여성"], index=0, horizontal=True)
            age = st.number_input("나이 (세)", min_value=1, max_value=120, value=45)
            height = st.number_input("신장 (cm)", min_value=50, max_value=250, value=173)
            weight = st.number_input("체중 (kg)", min_value=10, max_value=300, value=68)
            
            activity_levels = [
                "활동 거의 없음", 
                "가벼운 활동 (주 1~3회)", 
                "보통 활동 (주 3~5회)", 
                "많은 활동 (주 6~7회)"
            ]
            activity = st.selectbox("활동 수준", activity_levels, index=0)
            
            # BMR & TDEE Calculations using Mifflin-St Jeor Formula
            if gender == "남성":
                bmr = 10.0 * weight + 6.25 * height - 5.0 * age + 5.0
            else:
                bmr = 10.0 * weight + 6.25 * height - 5.0 * age - 161.0
                
            activity_factor = 1.2
            if activity == "가벼운 활동 (주 1~3회)":
                activity_factor = 1.375
            elif activity == "보통 활동 (주 3~5회)":
                activity_factor = 1.55
            elif activity == "많은 활동 (주 6~7회)":
                activity_factor = 1.725
                
            tdee = bmr * activity_factor
            
            # Carbs goals targets (Standard: 50% energy, Low-carb: 35% energy)
            # 1g carb = 4 kcal
            standard_carbs = (tdee * 0.50) / 4.0
            low_carbs = (tdee * 0.35) / 4.0
            
        with st.container(border=True):
            st.markdown("### 칼로리 및 영양 분석 결과")
            
            col_bmr_lbl, col_bmr_val = st.columns(2)
            with col_bmr_lbl:
                st.markdown("기초 대사량 (BMR)")
            with col_bmr_val:
                st.markdown(f"<p style='text-align:right; font-weight:bold;'>{int(bmr)} kcal</p>", unsafe_allow_html=True)
                
            col_tdee_lbl, col_tdee_val = st.columns(2)
            with col_tdee_lbl:
                st.markdown("일일 총 대사량 (TDEE)")
            with col_tdee_val:
                st.markdown(f"<p style='text-align:right; font-weight:bold; color:#2DD4BF;'>{int(tdee)} kcal</p>", unsafe_allow_html=True)
                
            st.markdown("<hr style='margin: 0.5rem 0;'/>", unsafe_allow_html=True)
            
            # Diet Targets
            st.markdown(f"""
            <div style='background-color:#0F172A; border-radius:8px; padding:12px; margin-bottom:12px;'>
                <span style='color:#94A3B8; font-size:11px;'>표준 탄수화물 식단 (50% 칼로리)</span><br/>
                <div style='display:flex; justify-content:space-between; align-items:center; margin-top:4px;'>
                    <span style='color:#F8FAFC; font-size:14px;'>하루 권장량</span>
                    <strong style='color:#F59E0B; font-size:18px;'>{int(standard_carbs)} g / 하루</strong>
                </div>
                <span style='color:#64748B; font-size:11px;'>끼니당 평균 약 {int(standard_carbs / 3.0)}g 분배 권장</span>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown(f"""
            <div style='background-color:#0F172A; border-radius:8px; padding:12px; margin-bottom:4px;'>
                <span style='color:#94A3B8; font-size:11px;'>저탄수화물 식단 (35% 칼로리)</span><br/>
                <div style='display:flex; justify-content:space-between; align-items:center; margin-top:4px;'>
                    <span style='color:#F8FAFC; font-size:14px;'>하루 권장량</span>
                    <strong style='color:#2DD4BF; font-size:18px;'>{int(low_carbs)} g / 하루</strong>
                </div>
                <span style='color:#64748B; font-size:11px;'>끼니당 평균 약 {int(low_carbs / 3.0)}g 분배 권장</span>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("<span style='font-size:10px; color:#64748B; line-height:1.4;'>참조 사이트: calculator.net Carbohydrate Calculator 가이드라인을 기반하여 계산되었습니다.</span>", unsafe_allow_html=True)

# ----------------------------------------------------
# TAB 2: HISTORY SCREEN (📋 투약기록)
# ----------------------------------------------------
elif st.session_state.active_tab == 2:
    logs = load_logs()
    
    # Stats header card
    with st.container(border=True):
        col_hist_hdr, col_hist_clear = st.columns([3, 1])
        with col_hist_hdr:
            st.markdown("### 투약 기록 통계 요약")
        with col_hist_clear:
            if logs:
                if st.button("❌ 기록 비우기", key="clear_all_logs_btn", use_container_width=True):
                    # Show streamlit warning confirmation by state
                    st.session_state.show_clear_confirm = True
                    
        # Confirmation flag
        if st.session_state.get("show_clear_confirm", False):
            st.warning("⚠️ 정말로 저장된 모든 투약 로그를 영구 삭제하시겠습니까?")
            c_cols = st.columns(2)
            with c_cols[0]:
                if st.button("예, 삭제합니다", key="confirm_clear_yes", type="primary", use_container_width=True):
                    clear_logs()
                    st.session_state.show_clear_confirm = False
                    st.toast("모든 로그가 초기화되었습니다.")
                    st.rerun()
            with c_cols[1]:
                if st.button("취소", key="confirm_clear_no", use_container_width=True):
                    st.session_state.show_clear_confirm = False
                    st.rerun()
                    
        st.markdown("<hr style='margin: 0.5rem 0;'/>", unsafe_allow_html=True)
        
        # Stats figures
        avg_bg = 0
        tot_ins = 0.0
        tot_carbs = 0.0
        if logs:
            avg_bg = int(sum(rec['currentGlucose'] for rec in logs) / len(logs))
            tot_ins = sum(rec['finalDose'] for rec in logs)
            tot_carbs = sum(rec['carbs'] for rec in logs)
            
        h_cols = st.columns(3)
        with h_cols[0]:
            st.markdown(f"<div style='text-align:center;'><span style='color:#94A3B8; font-size:11px;'>기록 평균 혈당</span><br/><strong style='font-size:16px;'>{avg_bg if logs else '--'} mg/dL</strong></div>", unsafe_allow_html=True)
        with h_cols[1]:
            st.markdown(f"<div style='text-align:center;'><span style='color:#94A3B8; font-size:11px;'>총 인슐린 투여</span><br/><strong style='color:#F59E0B; font-size:16px;'>{tot_ins:.1f if logs else '--'} U</strong></div>", unsafe_allow_html=True)
        with h_cols[2]:
            st.markdown(f"<div style='text-align:center;'><span style='color:#94A3B8; font-size:11px;'>총 탄수화물 섭취</span><br/><strong style='color:#2DD4BF; font-size:16px;'>{int(tot_carbs) if logs else '--'} g</strong></div>", unsafe_allow_html=True)
            
    # Timeline items list
    if not logs:
        st.markdown("<br/><br/>", unsafe_allow_html=True)
        st.markdown("<div style='text-align:center; color:#64748B;'>🛈 저장된 투약 로그가 없습니다.<br/>인슐린 계산기에서 투약을 기록해 보세요.</div>", unsafe_allow_html=True)
    else:
        for rec in logs:
            timestamp = float(rec['timestamp'])
            dt_str = datetime.datetime.fromtimestamp(timestamp / 1000.0).strftime('%Y-%m-%d %H:%M')
            glucose_val = int(rec['currentGlucose'])
            
            with st.container(border=True):
                # Header row
                col_time, col_bg_tag = st.columns([2, 1])
                with col_time:
                    st.markdown(f"<span style='color:#64748B; font-size:12px;'>{dt_str}</span>", unsafe_allow_html=True)
                with col_bg_tag:
                    badge_html = get_glucose_badge_html(glucose_val)
                    st.markdown(f"<div style='text-align:right;'>{badge_html} <strong style='font-size:14px; color:#F8FAFC; margin-left:4px;'>{glucose_val} mg/dL</strong></div>", unsafe_allow_html=True)
                    
                st.markdown("<hr style='margin: 0.35rem 0; opacity:0.3;'/>", unsafe_allow_html=True)
                
                # Image attachments row
                photo_before = rec.get('photoBefore', '')
                photo_after = rec.get('photoAfter', '')
                
                # Render photos thumbnails side by side
                photo_cols = st.columns(2)
                
                # Before photo thumbnail
                with photo_cols[0]:
                    if photo_before and os.path.exists(photo_before):
                        try:
                            img_b = Image.open(photo_before)
                            st.image(img_b, caption="식사 전", width=80)
                        except Exception:
                            st.markdown("<span style='color:#64748B; font-size:11px;'>식전 사진 로드 에러</span>", unsafe_allow_html=True)
                    else:
                        st.markdown("<span style='color:#64748B; font-size:11px;'>등록된 식전 사진 없음</span>", unsafe_allow_html=True)
                        
                # After photo thumbnail / upload trigger
                with photo_cols[1]:
                    if photo_after and os.path.exists(photo_after):
                        try:
                            img_a = Image.open(photo_after)
                            st.image(img_a, caption="식사 후", width=80)
                        except Exception:
                            st.markdown("<span style='color:#64748B; font-size:11px;'>식후 사진 로드 에러</span>", unsafe_allow_html=True)
                    else:
                        # Photo After uploader widget specific to this timestamp
                        ph_after_file = st.file_uploader("식사 후 사진 추가", type=["png", "jpg", "jpeg"], key=f"upload_after_{timestamp}", label_visibility="collapsed")
                        if ph_after_file:
                            local_path = save_uploaded_file(ph_after_file, "after")
                            update_log_after_photo(timestamp, local_path)
                            st.toast("식후 사진이 등록되었습니다.")
                            time.sleep(1)
                            st.rerun()
                            
                # Parameter Details
                col_params, col_bubble = st.columns([3, 1])
                with col_params:
                    st.markdown(f"<span style='color:#94A3B8; font-size:12px;'>식사 탄수화물: {int(rec['carbs'])}g" + (f" | 식후 운동: {rec['exerciseName']}" if rec['exerciseDuration'] > 0 else "") + "</span>", unsafe_allow_html=True)
                    reduction_text = f" | 운동감소: -{rec['exerciseReduction']:.1f}U" if rec['exerciseReduction'] > 0.0 else ""
                    st.markdown(f"<span style='color:#64748B; font-size:11px;'>식사: {rec['foodDose']:.1f}U | 교정: {rec['correctionDose']:.1f}U{reduction_text}</span>", unsafe_allow_html=True)
                with col_bubble:
                    # Final Dose Bubble
                    bubble_html = f"""
                    <div style='
                        background-color: rgba(245, 158, 11, 0.15);
                        border: 1px solid #F59E0B;
                        border-radius: 8px;
                        padding: 4px 8px;
                        text-align: center;
                        font-weight: bold;
                        color: #F59E0B;
                        font-size: 14px;
                    '>{rec['finalDose']:.1f} U</div>
                    """
                    st.markdown(bubble_html, unsafe_allow_html=True)
                    
                # Collapsible ICR Tuner Feedback
                with st.expander("식후 피드백 및 탄수화물 계수(ICR) 튜너"):
                    post_bg_input = st.text_input("식후 2시간 실제 혈당 (mg/dL)", value="", key=f"post_bg_input_{timestamp}")
                    if post_bg_input.strip().isdigit():
                        post_bg_val = int(post_bg_input.strip())
                        target_post = 180.0
                        isf = cur_settings.get("isf", 50.0)
                        
                        if post_bg_val > 200:
                            # Underdosed: blood glucose higher than 180 mg/dL target
                            excess_bg = post_bg_val - target_post
                            shortage_ins = excess_bg / isf
                            ideal_meal_dose = float(rec['foodDose']) + shortage_ins
                            
                            # Suggested new ICR = Carbs / ideal_meal_dose
                            suggested_icr = rec['carbs'] / ideal_meal_dose if ideal_meal_dose > 0.1 else cur_settings['icr']
                            suggested_icr = round(suggested_icr, 1)
                            
                            st.error(f"⚠️ 인슐린 투여량이 부족했습니다. (식후 혈당: {post_bg_val} mg/dL)")
                            st.write("식후 혈당이 목표 수치보다 높아 인슐린이 부족했음을 의미합니다. 탄수화물 계수(ICR) 강도를 더 높일 것을 추천합니다.")
                            
                            st.markdown(f"**권장 ICR**: {cur_settings['icr']} → **{suggested_icr} g/U**")
                            if st.button("설정 적용", key=f"apply_icr_{timestamp}"):
                                cur_settings['icr'] = suggested_icr
                                save_settings(cur_settings)
                                st.session_state.settings = cur_settings
                                st.toast(f"새로운 탄수화물 계수({suggested_icr})가 저장되었습니다.")
                                time.sleep(1)
                                st.rerun()
                                
                        elif post_bg_val < 70:
                            # Overdosed: hypoglycemia risk
                            deficit_bg = target_post - post_bg_val
                            excess_ins = deficit_bg / isf
                            ideal_meal_dose = max(0.5, float(rec['foodDose']) - excess_ins)
                            
                            suggested_icr = rec['carbs'] / ideal_meal_dose
                            suggested_icr = round(suggested_icr, 1)
                            
                            st.error(f"🚨 인슐린이 과다 투여되었습니다 (저혈당 위험). (식후 혈당: {post_bg_val} mg/dL)")
                            st.write("식후 혈당이 과도하게 하강하였습니다. 탄수화물 계수(ICR)를 증가시켜 인슐린 투여 강도를 완화할 것을 권장합니다.")
                            
                            st.markdown(f"**권장 ICR**: {cur_settings['icr']} → **{suggested_icr} g/U**")
                            if st.button("설정 적용", key=f"apply_icr_low_{timestamp}"):
                                cur_settings['icr'] = suggested_icr
                                save_settings(cur_settings)
                                st.session_state.settings = cur_settings
                                st.toast(f"새로운 탄수화물 계수({suggested_icr})가 저장되었습니다.")
                                time.sleep(1)
                                st.rerun()
                        else:
                            st.success(f"🟢 이상적인 혈당 제어 성공! (식후 혈당: {post_bg_val} mg/dL)")
                            st.write(f"탄수화물 계수({cur_settings['icr']})가 적절합니다.")

# ----------------------------------------------------
# TAB 3: SETTINGS SCREEN (⚙️ 환경설정)
# ----------------------------------------------------
elif st.session_state.active_tab == 3:
    # Group 1: Core coefficients
    with st.container(border=True):
        st.markdown("### 의학 기초 매개변수 설정")
        
        target_input = st.number_input("식사 전 목표 혈당 (mg/dL)", min_value=1, max_value=500, value=int(cur_settings.get("targetGlucose", 120)))
        icr_input = st.number_input("탄수화물 계수 (ICR - 1U당 탄수화물g)", min_value=0.1, max_value=100.0, value=float(cur_settings.get("icr", 10.0)), step=0.1)
        isf_input = st.number_input("혈당 교정 계수 (ISF - 1U당 낮추는 혈당)", min_value=0.1, max_value=500.0, value=float(cur_settings.get("isf", 50.0)), step=0.1)

    # Group 2: Rounding mode selector
    with st.container(border=True):
        st.markdown("### 인슐린 용량 반올림 설정")
        st.write("주사기나 펜의 정밀도에 맞춰 계산 결과를 반올림합니다.")
        
        round_modes = ["NONE", "0.5", "1.0"]
        round_mode_labels = ["무반올림", "0.5 U 단위", "1.0 U 단위"]
        
        round_idx = round_modes.index(cur_settings.get("roundingMode", "0.5"))
        rounding_val = st.radio("반올림 옵션", options=round_modes, index=round_idx, format_func=lambda x: round_mode_labels[round_modes.index(x)], horizontal=True)

    # Group 3: Custom exercise reductions
    with st.container(border=True):
        st.markdown("### 운동에 따른 인슐린 감량 비율 설정")
        
        walk30_rate = st.slider("식후 30분 걷기 감량율 (%)", min_value=0, max_value=80, value=int(cur_settings.get("walking30Reduction", 0.15) * 100)) / 100.0
        walk60_rate = st.slider("식후 1시간 걷기 감량율 (%)", min_value=0, max_value=80, value=int(cur_settings.get("walking60Reduction", 0.25) * 100)) / 100.0
        run30_rate = st.slider("식후 30분 달리기 감량율 (%)", min_value=0, max_value=80, value=int(cur_settings.get("running30Reduction", 0.35) * 100)) / 100.0
        run60_rate = st.slider("식후 1시간 달리기 감량율 (%)", min_value=0, max_value=80, value=int(cur_settings.get("running60Reduction", 0.50) * 100)) / 100.0

    # Group 4: LibreView sync setting
    with st.container(border=True):
        st.markdown("### LibreView (Libre LinkUp) 연동 설정")
        st.write("FreeStyle Libre 연속혈당측정기 계정을 연동하여 최근 일주일간의 혈당 변화 그래프와 당화혈색소 추정치를 가져옵니다.")
        
        l_email = st.text_input("Libre LinkUp 이메일 주소", value=cur_settings.get("libreEmail", ""))
        l_pass = st.text_input("비밀번호", value=cur_settings.get("librePassword", ""), type="password")
        
        regions = ["ap", "us", "eu", "de", "fr", "jp", "ae"]
        region_labels = ["한국/아태 (ap)", "미국 (us)", "유럽 (eu)", "독일 (de)", "프랑스 (fr)", "일본 (jp)", "아랍에미리트 (ae)"]
        reg_idx = regions.index(cur_settings.get("libreRegion", "ap"))
        l_region = st.selectbox("서브 지역 선택", options=regions, index=reg_idx, format_func=lambda x: region_labels[regions.index(x)])
        
        st.markdown("<hr style='margin: 0.5rem 0; opacity: 0.3;'/>", unsafe_allow_html=True)
        
        # Connection status indicators
        is_conn = cur_settings.get("libreConnected", False)
        conn_badge_color = "#10B981" if is_conn else "#F59E0B"
        conn_text = "연결됨 (실제 데이터)" if is_conn else "데모 모드 (가상 데이터)"
        
        col_conn_stat, col_conn_disc = st.columns([3, 1])
        with col_conn_stat:
            st.markdown(f"**연결 상태**: <span style='color:{conn_badge_color}; font-weight:bold;'>{conn_text}</span>", unsafe_allow_html=True)
            last_sync_ms = cur_settings.get("libreLastSyncTime", 0)
            if last_sync_ms > 0:
                last_sync_str = datetime.datetime.fromtimestamp(last_sync_ms / 1000.0).strftime('%m-%d %H:%M')
                st.markdown(f"<span style='color:#64748B; font-size:11px;'>최근 동기화: {last_sync_str}</span>", unsafe_allow_html=True)
        with col_conn_disc:
            if is_conn:
                if st.button("연동 해제", key="disconnect_libre_btn", use_container_width=True):
                    cur_settings["libreEmail"] = ""
                    cur_settings["librePassword"] = ""
                    cur_settings["libreConnected"] = False
                    cur_settings["libreLastSyncTime"] = 0
                    save_settings(cur_settings)
                    st.session_state.settings = cur_settings
                    generate_mock_libre_data() # Reset back to mock data
                    st.toast("연동 해제 및 데모 데이터로 전환되었습니다.", icon="🔌")
                    time.sleep(1)
                    st.rerun()
                    
        # Error alert
        if st.session_state.sync_error:
            st.error(f"❌ {st.session_state.sync_error}")
            
        # Sync immediately
        if st.button("LibreView 동기화 시작", type="primary", key="sync_now_settings_btn", use_container_width=True):
            cur_settings["libreEmail"] = l_email
            cur_settings["librePassword"] = l_pass
            cur_settings["libreRegion"] = l_region
            save_settings(cur_settings)
            
            st.session_state.is_syncing = True
            st.session_state.sync_error = None
            
            client = LibreLinkUpClient()
            res = client.fetch_recent_glucose(l_email, l_pass, l_region)
            
            st.session_state.is_syncing = False
            if res.get("success"):
                save_glucose(res.get("readings", []))
                cur_settings["libreConnected"] = True
                cur_settings["libreLastSyncTime"] = int(time.time() * 1000)
                cur_settings["libreHbA1c"] = float(res.get("est_hba1c", 7.6))
                cur_settings["libreAvgGlucose"] = float(res.get("avg_glucose", 176.0))
                save_settings(cur_settings)
                st.session_state.settings = cur_settings
                st.toast("LibreView 데이터 동기화 완료!", icon="✅")
                time.sleep(1)
                st.rerun()
            else:
                st.session_state.sync_error = res.get("message")
                st.rerun()

    # Save button
    if st.button("설정 저장", type="primary", key="save_general_settings_btn"):
        if target_input <= 0 or icr_input <= 0.0 or isf_input <= 0.0:
            st.error("올바른 숫자를 입력하세요. 계수는 0보다 커야 합니다.")
        else:
            cur_settings["targetGlucose"] = int(target_input)
            cur_settings["icr"] = float(icr_input)
            cur_settings["isf"] = float(isf_input)
            cur_settings["roundingMode"] = rounding_val
            cur_settings["walking30Reduction"] = walk30_rate
            cur_settings["walking60Reduction"] = walk60_rate
            cur_settings["running30Reduction"] = run30_rate
            cur_settings["running60Reduction"] = run60_rate
            cur_settings["libreEmail"] = l_email
            cur_settings["librePassword"] = l_pass
            cur_settings["libreRegion"] = l_region
            
            save_settings(cur_settings)
            st.session_state.settings = cur_settings
            st.toast("설정이 성공적으로 저장되었습니다!", icon="💾")
            time.sleep(1)
            st.rerun()

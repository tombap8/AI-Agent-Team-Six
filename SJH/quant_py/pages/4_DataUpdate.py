import streamlit as st
import pandas as pd
import subprocess
import sys
import os
from utils.db_helper import get_engine, get_connection
from utils.sample_generator import generate_sample_data

# Page Config
st.set_page_config(page_title="데이터 관리 - Citrus Quant", page_icon="🍋", layout="wide")

# Custom CSS styling (reuse theme styling)
st.markdown("""
<style>
    .stApp { background-color: #F7F9FA; }
    .citrus-card {
        background-color: #FFFFFF;
        border-radius: 16px;
        padding: 24px;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.04), 0 4px 6px -4px rgba(0, 0, 0, 0.04);
        border: 1px solid #F1F5F9;
        margin-bottom: 20px;
    }
    .accent-text { color: #00C49F; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

st.title("⚙️ 데이터베이스 관리 & 수집 파이프라인")
st.markdown("수집된 주식 데이터의 테이블별 상태를 점검하고 새로운 데이터를 크롤링하거나 샘플 데이터를 적재합니다.")

# 1. Database Table Status Function
def get_db_stats():
    engine = get_engine()
    stats = []
    tables = {
        'kor_ticker': '기초 티커 정보',
        'kor_sector': '종목 섹터 정보',
        'kor_price': '일별 가격 데이터',
        'kor_fs': '재무제표 원본 데이터',
        'kor_value': '가치평가 지표',
        'kor_multi_factor': '종합 QVM 분석 데이터'
    }
    
    try:
        with engine.connect() as conn:
            for t_name, t_desc in tables.items():
                try:
                    df_count = pd.read_sql(f"SELECT COUNT(*) as cnt FROM {t_name}", con=conn)
                    row_cnt = df_count['cnt'].iloc[0]
                    
                    # Try checking dates
                    if t_name == 'kor_price':
                        df_dates = pd.read_sql(f"SELECT MIN(날짜) as mind, MAX(날짜) as maxd FROM {t_name}", con=conn)
                        date_range = f"{df_dates['mind'].iloc[0]} ~ {df_dates['maxd'].iloc[0]}"
                    else:
                        df_dates = pd.read_sql(f"SELECT MIN(기준일) as mind, MAX(기준일) as maxd FROM {t_name}", con=conn)
                        date_range = f"{df_dates['mind'].iloc[0]} ~ {df_dates['maxd'].iloc[0]}"
                except Exception:
                    row_cnt = 0
                    date_range = "N/A"
                    
                stats.append({
                    "테이블 명": t_name,
                    "테이블 설명": t_desc,
                    "레코드 수": f"{row_cnt:,} 건",
                    "적재 기간": date_range
                })
    except Exception as e:
        st.error(f"DB 통계 조회 실패: {e}")
    finally:
        engine.dispose()
        
    return pd.DataFrame(stats)

# Display DB Stats
st.markdown("<div class='citrus-card'>", unsafe_allow_html=True)
st.markdown("### 📊 데이터베이스 현황")
df_stats = get_db_stats()
if not df_stats.empty:
    st.table(df_stats)
st.markdown("</div>", unsafe_allow_html=True)

# Function to run python scrapers with real-time logging
def run_scraper_script(script_path):
    st.info(f"👉 스크립트 실행 중: {script_path}...")
    
    # Create console placeholder
    console_placeholder = st.empty()
    console_logs = []
    
    # Run the script via python subprocess
    # Cwd set to project root to allow relative packages
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    full_path = os.path.join(root_dir, script_path)
    
    process = subprocess.Popen(
        [sys.executable, full_path],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding='utf-8',
        errors='replace',
        cwd=root_dir
    )
    
    while True:
        line = process.stdout.readline()
        if not line and process.poll() is not None:
            break
        if line:
            console_logs.append(line.strip())
            # Truncate logs to avoid overloading web UI
            if len(console_logs) > 100:
                console_logs.pop(0)
            console_placeholder.code("\n".join(console_logs))
            
    rc = process.poll()
    if rc == 0:
        st.success(f"✅ {script_path} 실행 완료!")
        return True
    else:
        st.error(f"❌ {script_path} 실행 실패 (종료 코드: {rc})")
        return False

# Actions Section
col1, col2 = st.columns(2)

with col1:
    st.markdown("<div class='citrus-card'>", unsafe_allow_html=True)
    st.markdown("### 🚀 샘플 데이터 로드")
    st.markdown("데이터베이스가 비어있거나 테스트용 가상 데이터를 빠르게 구성하고 싶을 때 사용합니다.")
    
    if st.button("🍋 샘플 데이터 생성 (3초 소요)", use_container_width=True):
        with st.spinner("테이블 청소 및 샘플 데이터 적재 중..."):
            generate_sample_data()
            st.success("🎉 성공적으로 30대 기업의 가상 1개년 주가 및 팩터 데이터가 생성되었습니다!")
            st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

with col2:
    st.markdown("<div class='citrus-card'>", unsafe_allow_html=True)
    st.markdown("### 🔍 실시간 데이터 수집 파이프라인")
    st.markdown("네이버 금융 및 KRX를 통해 실시간으로 2000여 종목의 최신 퀀트 데이터를 처음부터 수집합니다.")
    
    run_all_pipelines = st.button("💻 전체 데이터 수집 시작 (20분 소요)", use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

if run_all_pipelines:
    st.markdown("<div class='citrus-card'>", unsafe_allow_html=True)
    st.markdown("### 💻 수집 스크립트 콘솔 출력")
    
    scripts = [
        "1.KOR_TICKER&SECTOR.py",
        "2.KOR_PRICE.py",
        "3.KOR_FS&VALUE.py",
        "4.KOR_VALUE(공시구분 y).py",
        "5.kor_fs_value.py"
    ]
    
    success = True
    for idx, s in enumerate(scripts):
        st.write(f"**[{idx+1}/{len(scripts)}]** {s}")
        if not run_scraper_script(s):
            success = False
            break
            
    if success:
        st.balloons()
        st.success("🎉 전체 퀀트 주식 정보 데이터 파이프라인 수집 완료!")
        st.rerun()
    else:
        st.error("데이터 수집 중 오류가 발생해 중단되었습니다. 콘솔 로그를 확인하세요.")
        
    st.markdown("</div>", unsafe_allow_html=True)

import streamlit as st
import pandas as pd
from utils.db_helper import get_engine

# 1. Page Configuration
st.set_page_config(
    page_title="시트러스 퀀트 포트폴리오 (Citrus Quant)",
    page_icon="🍋",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Custom CSS Injection (Bright, Fresh Citrus & Mint Theme)
st.markdown("""
<style>
    /* Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&family=Outfit:wght@500;700&family=Noto+Sans+KR:wght@400;500;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', 'Noto Sans KR', sans-serif;
    }
    
    /* Main Background */
    .stApp {
        background-color: #F7F9FA;
    }
    
    /* Sidebar styling */
    section[data-testid="stSidebar"] {
        background-color: #FFFFFF !important;
        border-right: 1px solid #E2E8F0;
    }
    section[data-testid="stSidebar"] h1 {
        color: #00C49F !important;
        font-family: 'Outfit', sans-serif;
        font-weight: 700;
    }
    
    /* Custom Card Style */
    .citrus-card {
        background-color: #FFFFFF;
        border-radius: 16px;
        padding: 24px;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.04), 0 4px 6px -4px rgba(0, 0, 0, 0.04);
        border: 1px solid #F1F5F9;
        margin-bottom: 20px;
    }
    
    /* Metrics display */
    div[data-testid="stMetric"] {
        background-color: #FFFFFF;
        border-radius: 12px;
        padding: 16px;
        border: 1px solid #F1F5F9;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.02);
    }
    
    /* Header Accent */
    .accent-title {
        color: #00C49F !important;
        font-family: 'Outfit', sans-serif;
        font-weight: 700;
    }
    
    /* Success & Fresh alerts */
    .stAlert {
        border-radius: 12px !important;
    }
</style>
""", unsafe_allow_html=True)

# 3. Sidebar Header
st.sidebar.markdown("<h1 style='text-align: center;'>🍋 Citrus Quant</h1>", unsafe_allow_html=True)
st.sidebar.info("상큼하고 직관적인 퀀트투자 포트폴리오 웹 프로그램입니다. 사이드바 메뉴를 이용해 다른 페이지로 이동해 주세요.")

# 4. Main Page Body
st.markdown("<h1>🍋 <span class='accent-title'>Citrus Quant</span> 포트폴리오 관리 시스템</h1>", unsafe_allow_html=True)
st.markdown("<p style='color:#64748B; font-size:16px;'>데이터 분석과 시각화를 바탕으로 선별된 상위 퀄리티/밸류/모멘텀(QVM) 퀀트 포트폴리오를 관리하고 성과를 백테스트합니다.</p>", unsafe_allow_html=True)

st.markdown("---")

# 5. Database Status Check
engine = get_engine()
db_status_kor = {}
db_status_global = {}
latest_date_kor = None
latest_date_global = None

try:
    with engine.connect() as conn:
        # KOR Tables
        for t in ['kor_ticker', 'kor_sector', 'kor_price', 'kor_fs', 'kor_multi_factor']:
            try:
                df_count = pd.read_sql(f"SELECT COUNT(*) as cnt FROM {t}", con=conn)
                db_status_kor[t] = df_count['cnt'].iloc[0]
            except Exception:
                db_status_kor[t] = 0
                
        # Global Tables
        for t in ['global_ticker', 'global_sector', 'global_price', 'global_fs', 'global_multi_factor']:
            try:
                df_count = pd.read_sql(f"SELECT COUNT(*) as cnt FROM {t}", con=conn)
                db_status_global[t] = df_count['cnt'].iloc[0]
            except Exception:
                db_status_global[t] = 0
            
        try:
            latest_date_df = pd.read_sql("SELECT MAX(기준일) as max_date FROM kor_ticker", con=conn)
            latest_date_kor = latest_date_df['max_date'].iloc[0]
        except Exception:
            latest_date_kor = None
            
        try:
            latest_date_df = pd.read_sql("SELECT MAX(기준일) as max_date FROM global_ticker", con=conn)
            latest_date_global = latest_date_df['max_date'].iloc[0]
        except Exception:
            latest_date_global = None
except Exception as e:
    st.error(f"데이터베이스 연결 오류: {e}")
    db_status_kor = None
    db_status_global = None
finally:
    engine.dispose()

has_data = (db_status_kor and sum(db_status_kor.values()) > 0) or (db_status_global and sum(db_status_global.values()) > 0)

if has_data:
    # Database is populated
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("<div class='citrus-card'>", unsafe_allow_html=True)
        st.markdown("### 🇰🇷 국내 주식 시장 현황 (KOSPI)")
        
        kor_date_str = str(latest_date_kor) if latest_date_kor else "N/A"
        kor_price_str = f"{db_status_kor.get('kor_price', 0):,}"
        kor_ticker_str = f"{db_status_kor.get('kor_ticker', 0)}"
        
        st.markdown(f"""
        <div style="display: flex; justify-content: space-between; align-items: center; gap: 12px; margin-top: 15px;">
            <div style="flex: 1; min-width: 0; background-color: #F0FDFA; padding: 16px 12px; border-radius: 12px; border: 1px solid #CCFBF1; text-align: center;">
                <div style="color: #0D9488; font-size: 13px; font-weight: 600; white-space: nowrap;">보통주 수</div>
                <div style="color: #111827; font-size: 20px; font-weight: 700; margin-top: 6px; white-space: nowrap;">{kor_ticker_str} 개</div>
            </div>
            <div style="flex: 1; min-width: 0; background-color: #F0FDFA; padding: 16px 12px; border-radius: 12px; border: 1px solid #CCFBF1; text-align: center;">
                <div style="color: #0D9488; font-size: 13px; font-weight: 600; white-space: nowrap;">총 가격 건수</div>
                <div style="color: #111827; font-size: 20px; font-weight: 700; margin-top: 6px; white-space: nowrap;">{kor_price_str} 건</div>
            </div>
            <div style="flex: 1; min-width: 0; background-color: #F0FDFA; padding: 16px 12px; border-radius: 12px; border: 1px solid #CCFBF1; text-align: center;">
                <div style="color: #0D9488; font-size: 13px; font-weight: 600; white-space: nowrap;">최신 일자</div>
                <div style="color: #111827; font-size: 20px; font-weight: 700; margin-top: 6px; white-space: nowrap;">{kor_date_str}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
        
    with col2:
        st.markdown("<div class='citrus-card'>", unsafe_allow_html=True)
        st.markdown("### 🇺🇸 해외 주식 시장 현황 (US)")
        
        global_date_str = str(latest_date_global) if latest_date_global else "N/A"
        global_price_str = f"{db_status_global.get('global_price', 0):,}"
        global_ticker_str = f"{db_status_global.get('global_ticker', 0)}"
        
        st.markdown(f"""
        <div style="display: flex; justify-content: space-between; align-items: center; gap: 12px; margin-top: 15px;">
            <div style="flex: 1; min-width: 0; background-color: #F0FDFA; padding: 16px 12px; border-radius: 12px; border: 1px solid #CCFBF1; text-align: center;">
                <div style="color: #0D9488; font-size: 13px; font-weight: 600; white-space: nowrap;">보통주 수</div>
                <div style="color: #111827; font-size: 20px; font-weight: 700; margin-top: 6px; white-space: nowrap;">{global_ticker_str} 개</div>
            </div>
            <div style="flex: 1; min-width: 0; background-color: #F0FDFA; padding: 16px 12px; border-radius: 12px; border: 1px solid #CCFBF1; text-align: center;">
                <div style="color: #0D9488; font-size: 13px; font-weight: 600; white-space: nowrap;">총 가격 건수</div>
                <div style="color: #111827; font-size: 20px; font-weight: 700; margin-top: 6px; white-space: nowrap;">{global_price_str} 건</div>
            </div>
            <div style="flex: 1; min-width: 0; background-color: #F0FDFA; padding: 16px 12px; border-radius: 12px; border: 1px solid #CCFBF1; text-align: center;">
                <div style="color: #0D9488; font-size: 13px; font-weight: 600; white-space: nowrap;">최신 일자</div>
                <div style="color: #111827; font-size: 20px; font-weight: 700; margin-top: 6px; white-space: nowrap;">{global_date_str}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
        
    st.markdown("<div class='citrus-card'>", unsafe_allow_html=True)
    st.markdown("### 📊 서비스 핵심 기능 소개")
    st.markdown("""
    - **1_Dashboard.py**: 국내 및 해외 주식의 섹터별 시가총액 트리맵을 비교 분석하고, 개별 종목의 캔들스틱 차트 및 **볼린저 밴드/RSI 기술 지표 오버레이**를 확인합니다.
    - **2_Screening.py**: 퀄리티, 밸류, 모멘텀 지표 가중치 슬라이더를 통해 실시간 QVM 종합 순위 Top 20 포트폴리오를 도출합니다.
    - **3_Backtest.py**: 선정된 종목의 최적 비중 산출 및 **주기별 리밸런싱 백테스트(거래 세금/수수료 차감)**와 증권사 API 연동용 **가상 주문 신호 시트(CSV)**를 다운로드합니다.
    - **4_DataUpdate.py**: 크롤링 스크립트를 관리하거나 테스트용 가상 데이터를 복원합니다.
    """)
    st.markdown("</div>", unsafe_allow_html=True)
    
    st.success("🎉 데이터베이스에 주식 데이터가 정상 적재되어 있습니다! 상단 또는 사이드바의 페이지 링크를 타고 이동하세요.")
else:
    # Database is empty
    st.markdown("<div class='citrus-card' style='border-left: 6px solid #FFD700;'>", unsafe_allow_html=True)
    st.markdown("### ⚠️ 데이터베이스가 비어 있습니다.")
    st.markdown("""
    현재 데이터베이스에 적재된 주식 정보가 없습니다. 앱의 모든 기능을 활용하시기 위해 두 가지 방법으로 데이터를 준비하실 수 있습니다.
    
    1. **샘플 데이터 로드 (추천 - 3초 소요)**: 주요 국내 및 미국 대형주의 1개년 가격과 팩터 데이터를 즉시 생성하여 대시보드를 바로 활성화합니다.
    2. **전체 시장 데이터 크롤링 (20분 소요)**: 크롤러 파이프라인을 실행해 데이터를 새로 수집합니다.
    
    사이드바에서 **`4_DataUpdate`** 페이지로 이동하여 데이터를 적재해 주세요!
    """)
    st.markdown("</div>", unsafe_allow_html=True)
    
    if st.button("👉 데이터 관리 & 수집 페이지로 즉시 이동하기"):
        st.info("사이드바의 '4_DataUpdate' 메뉴를 직접 클릭하여 데이터 수집을 시작하실 수 있습니다.")


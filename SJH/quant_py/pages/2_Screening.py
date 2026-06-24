import streamlit as st
import pandas as pd
import plotly.express as px
from utils.quant_helper import calculate_dynamic_qvm

# Page Config
st.set_page_config(page_title="퀀트 스크리닝 - Citrus Quant", page_icon="🍋", layout="wide")

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

st.title("🎯 QVM 퀀트 스크리닝")
st.markdown("퀄리티, 밸류, 모멘텀 팩터의 비중을 자유롭게 조율하여 실시간 종합 순위를 산출합니다.")

# 1. Market Selection
st.markdown("<div class='citrus-card'>", unsafe_allow_html=True)
market = st.selectbox(
    "조회할 시장을 선택하세요.",
    options=["🇰🇷 국내 주식 시장 (KOSPI)", "🇺🇸 해외 주식 시장 (US)"],
    index=0
)
market_code = "KOR" if "국내" in market else "US"
st.session_state['screened_market'] = market_code
st.markdown("</div>", unsafe_allow_html=True)

# 2. Sidebar Sliders for Factor Weights
st.sidebar.markdown("### 🎛️ 팩터 가중치 설정")
w_q_pct = st.sidebar.slider("퀄리티(Quality) 가중치 (%)", min_value=0, max_value=100, value=34, step=5)
w_v_pct = st.sidebar.slider("밸류(Value) 가중치 (%)", min_value=0, max_value=100, value=33, step=5)
w_m_pct = st.sidebar.slider("모멘텀(Momentum) 가중치 (%)", min_value=0, max_value=100, value=33, step=5)

# Normalization
total_pct = w_q_pct + w_v_pct + w_m_pct
if total_pct > 0:
    w_q = w_q_pct / total_pct
    w_v = w_v_pct / total_pct
    w_m = w_m_pct / total_pct
else:
    w_q = 0.33
    w_v = 0.33
    w_m = 0.34
    total_pct = 100

st.sidebar.markdown(f"**실제 반영 가중치:**\n- 퀄리티: {w_q*100:.1f}%\n- 밸류: {w_v*100:.1f}%\n- 모멘텀: {w_m*100:.1f}%")
if total_pct != 100:
    st.sidebar.warning(f"⚠️ 가중치 합이 {total_pct}%입니다. 자동으로 비율에 맞춰 100%로 보정되어 적용됩니다.")

# 3. Load sectors for market selection
try:
    df_raw = calculate_dynamic_qvm(w_q, w_v, w_m, market=market_code)
    if not df_raw.empty:
        sectors = sorted(df_raw['SEC_NM_KOR'].unique().tolist())
    else:
        sectors = []
except Exception:
    sectors = []

st.markdown("<div class='citrus-card'>", unsafe_allow_html=True)
selected_sectors = st.multiselect(
    "조회할 섹터를 선택하세요. (비워두면 전체 섹터를 조회합니다)",
    options=sectors,
    default=[]
)
st.markdown("</div>", unsafe_allow_html=True)

# 4. Dynamic Calculation
if not df_raw.empty:
    df_screened = calculate_dynamic_qvm(w_q, w_v, w_m, target_sectors=selected_sectors, market=market_code)
    
    if df_screened.empty:
        st.warning("선택한 조건에 맞는 종목이 없습니다.")
    else:
        # Get Top 20 stocks
        df_top20 = df_screened.head(20).copy()
        
        # Save to session state so Backtesting page can load them automatically
        st.session_state['screened_tickers'] = df_top20['종목코드'].tolist()
        st.session_state['screened_names'] = df_top20['종목명'].tolist()
        
        # Display Top 20 table
        st.markdown("<div class='citrus-card'>", unsafe_allow_html=True)
        st.markdown(f"### 🏆 실시간 QVM 종합 순위 Top 20 ({market_code} 시장)")
        st.markdown("퀄리티, 밸류, 모멘텀 점수를 합산하여 산출한 종합 상위 20개 종목입니다. (이 종목들은 **포트폴리오 최적화 및 백테스트** 탭으로 자동 연동됩니다)")
        
        # Clean dataframe for display
        df_display = df_top20[[
            '종목코드', '종목명', 'SEC_NM_KOR', 
            'z_quality', 'z_value', 'z_momentum', 'qvm'
        ]].copy()
        
        df_display.columns = ['종목코드', '종목명', '섹터', '퀄리티 점수', '밸류 점수', '모멘텀 점수', 'QVM 종합점수']
        df_display = df_display.round(3)
        df_display = df_display.reset_index(drop=True)
        df_display.index += 1
        
        st.dataframe(df_display, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Display factor distribution scatter plot
        st.markdown("<div class='citrus-card'>", unsafe_allow_html=True)
        st.markdown("### 📈 Top 20 팩터별 분포 현황")
        
        # Ensure sizes are positive for plotly scatter plot
        df_top20['qvm_size'] = df_top20['qvm'] - df_top20['qvm'].min() + 1
        
        fig_scatter = px.scatter(
            df_top20,
            x='z_value',
            y='z_quality',
            size='qvm_size',
            color='SEC_NM_KOR',
            hover_name='종목명',
            labels={
                'z_value': '밸류 점수 (Z-Score)',
                'z_quality': '퀄리티 점수 (Z-Score)',
                'qvm_size': 'QVM 종합점수 (상대크기)'
            },
            title='밸류 vs 퀄리티 (점수 크기는 QVM 종합점수 반영)'
        )
        st.plotly_chart(fig_scatter, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
else:
    st.warning("⚠️ 표시할 데이터가 없습니다. '4_DataUpdate' 페이지에서 데이터를 적재해 주세요.")

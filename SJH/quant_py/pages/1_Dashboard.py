import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from utils.db_helper import get_engine
from utils.quant_helper import get_technical_indicators

# Page Config
st.set_page_config(page_title="시장 대시보드 - Citrus Quant", page_icon="🍋", layout="wide")

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

st.title("📊 시장 및 섹터 대시보드")
st.markdown("수집된 보통주 데이터의 섹터 분포와 가치/재무 정보를 시각적으로 확인합니다.")

# 1. Market Selection Toggle
st.markdown("<div class='citrus-card'>", unsafe_allow_html=True)
market = st.selectbox(
    "조회할 시장을 선택하세요.",
    options=["🇰🇷 국내 주식 시장 (KOSPI)", "🇺🇸 해외 주식 시장 (US)"],
    index=0
)
market_code = "KOR" if "국내" in market else "US"
prefix = "kor" if market_code == "KOR" else "global"
st.markdown("</div>", unsafe_allow_html=True)

# DB connection and query
engine = get_engine()

try:
    # Query merged ticker & sector details based on market selection
    query = f"""
        SELECT t.종목코드, t.종목명, t.시장구분, t.종가, t.시가총액, s.SEC_NM_KOR
        FROM {prefix}_ticker t
        JOIN {prefix}_sector s ON t.종목코드 = s.CMP_CD
        WHERE t.기준일 = (SELECT MAX(기준일) FROM {prefix}_ticker)
          AND t.종목구분 = '보통주'
    """
    df_market = pd.read_sql(query, con=engine)
    
    # Query details for individual search
    query_all = f"""
        SELECT * FROM {prefix}_multi_factor
        WHERE 기준일 = (SELECT MAX(기준일) FROM {prefix}_multi_factor)
    """
    df_details = pd.read_sql(query_all, con=engine)
except Exception as e:
    st.error(f"데이터베이스 조회 중 오류 발생: {e}")
    df_market = pd.DataFrame()
    df_details = pd.DataFrame()
finally:
    engine.dispose()

if df_market.empty:
    st.warning("⚠️ 표시할 데이터가 없습니다. '4_DataUpdate' 페이지에서 데이터를 적재해 주세요.")
else:
    # Scale Market Cap
    if market_code == "KOR":
        df_market['시가총액(억원)'] = df_market['시가총액'] / 100000000
        val_suffix = "억원"
    else:
        df_market['시가총액(억달러)'] = df_market['시가총액'] / 100000000
        val_suffix = "억달러"
        
    # Sector distributions
    sector_summary = df_market.groupby('SEC_NM_KOR').agg(
        종목수=('종목코드', 'count'),
        시가총액합=(f"시가총액({val_suffix})", 'sum')
    ).reset_index()
    
    col1, col2 = st.columns([3, 2])
    
    with col1:
        st.markdown("<div class='citrus-card'>", unsafe_allow_html=True)
        st.markdown(f"### 🗺️ 섹터별 시가총액 트리맵 ({market_code})")
        fig_tree = px.treemap(
            df_market,
            path=['SEC_NM_KOR', '종목명'],
            values=f"시가총액({val_suffix})",
            color='SEC_NM_KOR',
            color_discrete_sequence=px.colors.qualitative.Pastel,
            title=f"시가총액 크기별 트리맵 분포 (단위: {val_suffix})"
        )
        fig_tree.update_layout(margin=dict(t=30, l=10, r=10, b=10))
        st.plotly_chart(fig_tree, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
        
    with col2:
        st.markdown("<div class='citrus-card'>", unsafe_allow_html=True)
        st.markdown(f"### 🍩 섹터별 종목수 비율 ({market_code})")
        fig_pie = px.pie(
            sector_summary,
            names='SEC_NM_KOR',
            values='종목수',
            hole=0.4,
            color_discrete_sequence=px.colors.qualitative.Pastel,
            title='전체 등록 종목의 섹터 비중'
        )
        fig_pie.update_layout(margin=dict(t=30, l=10, r=10, b=10))
        st.plotly_chart(fig_pie, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # Search and Technical Indicators section
    st.markdown("<div class='citrus-card'>", unsafe_allow_html=True)
    st.markdown("### 🔍 개별 종목 상세 퀀트 & 기술적 지표 조회")
    
    stock_search = st.selectbox(
        "조회할 종목명을 선택하세요.",
        options=df_details['종목명'].unique() if not df_details.empty else []
    )
    
    if stock_search and not df_details.empty:
        stock_data = df_details[df_details['종목명'] == stock_search].iloc[0]
        ticker = stock_data['종목코드']
        
        # 1. Metric Numbers
        scol1, scol2, scol3, scol4 = st.columns(4)
        with scol1:
            st.metric("종목코드", ticker)
            st.metric("소속 섹터", stock_data['SEC_NM_KOR'])
        with scol2:
            st.metric("PER (배)", f"{stock_data['PER']:.2f}" if pd.notnull(stock_data['PER']) else "N/A")
            st.metric("PBR (배)", f"{stock_data['PBR']:.2f}" if pd.notnull(stock_data['PBR']) else "N/A")
        with scol3:
            st.metric("ROE (%)", f"{stock_data['ROE']*100:.2f}%" if pd.notnull(stock_data['ROE']) else "N/A")
            st.metric("GPA (%)", f"{stock_data['GPA']*100:.2f}%" if pd.notnull(stock_data['GPA']) else "N/A")
        with scol4:
            st.metric("12M 수익률 (%)", f"{stock_data['12M']*100:.2f}%" if pd.notnull(stock_data['12M']) else "N/A")
            st.metric("K_ratio", f"{stock_data['K_ratio']:.2f}" if pd.notnull(stock_data['K_ratio']) else "N/A")
            
        st.markdown("---")
        
        # 2. Get technical indicator calculations
        df_tech = get_technical_indicators(ticker, market=market_code)
        
        if not df_tech.empty:
            st.markdown(f"#### 📈 {stock_search} ({ticker}) 기술적 분석 지표 (볼린저 밴드 & RSI 14)")
            
            # Create subplots (Row 1: Candlestick/SMA/BB, Row 2: RSI)
            fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                                vertical_spacing=0.08, 
                                row_heights=[0.7, 0.3])
            
            # BB Upper Line
            fig.add_trace(go.Scatter(
                x=df_tech['날짜'], y=df_tech['BB_Upper'], 
                line=dict(color='rgba(0, 196, 159, 0.2)', width=1), 
                name='BB Upper', showlegend=True
            ), row=1, col=1)
            
            # BB Lower Line & fill to upper
            fig.add_trace(go.Scatter(
                x=df_tech['날짜'], y=df_tech['BB_Lower'], 
                line=dict(color='rgba(0, 196, 159, 0.2)', width=1),
                fill='tonexty', fillcolor='rgba(0, 196, 159, 0.03)',
                name='Bollinger Area', showlegend=True
            ), row=1, col=1)
            
            # Candlestick
            fig.add_trace(go.Candlestick(
                x=df_tech['날짜'],
                open=df_tech['시가'],
                high=df_tech['고가'],
                low=df_tech['저가'],
                close=df_tech['종가'],
                increasing_line_color='#00C49F',
                decreasing_line_color='#FF6B6B',
                name='Price'
            ), row=1, col=1)
            
            # SMA 20
            fig.add_trace(go.Scatter(
                x=df_tech['날짜'], y=df_tech['SMA'],
                line=dict(color='#85E313', width=1.5),
                name='SMA 20'
            ), row=1, col=1)
            
            # Buy/Sell Signal Markers
            buys = df_tech[df_tech['Signal'] == 'BUY']
            sells = df_tech[df_tech['Signal'] == 'SELL']
            
            fig.add_trace(go.Scatter(
                x=buys['날짜'], y=buys['종가'],
                mode='markers',
                marker=dict(symbol='triangle-up', size=12, color='#00C49F', line=dict(width=1, color='black')),
                name='Buy Signal (BB Lower cross)'
            ), row=1, col=1)
            
            fig.add_trace(go.Scatter(
                x=sells['날짜'], y=sells['종가'],
                mode='markers',
                marker=dict(symbol='triangle-down', size=12, color='#FF6B6B', line=dict(width=1, color='black')),
                name='Sell Signal (BB Upper cross)'
            ), row=1, col=1)
            
            # Row 2: RSI
            fig.add_trace(go.Scatter(
                x=df_tech['날짜'], y=df_tech['RSI'],
                line=dict(color='#FFD700', width=1.5),
                name='RSI 14'
            ), row=2, col=1)
            
            # Add oversold/overbought lines
            fig.add_hline(y=70, line_dash="dash", line_color="rgba(255, 107, 107, 0.5)", row=2, col=1)
            fig.add_hline(y=30, line_dash="dash", line_color="rgba(0, 196, 159, 0.5)", row=2, col=1)
            
            fig.update_layout(
                height=550,
                xaxis_rangeslider_visible=False,
                margin=dict(t=30, l=10, r=10, b=10),
                legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01),
                hovermode="x unified"
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("해당 종목의 차트 주가 정보가 부족합니다.")
            
    st.markdown("</div>", unsafe_allow_html=True)

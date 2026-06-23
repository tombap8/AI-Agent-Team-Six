import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from utils.quant_helper import optimize_portfolio, run_backtest, calculate_dynamic_qvm, generate_order_signals

# Page Config
st.set_page_config(page_title="최적화 및 백테스트 - Citrus Quant", page_icon="🍋", layout="wide")

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
    .metric-val { color: #00C49F; font-size: 24px; font-weight: bold; }
    .metric-label { color: #64748B; font-size: 14px; }
</style>
""", unsafe_allow_html=True)

st.title("📈 포트폴리오 최적화 & 백테스팅")
st.markdown("선정된 퀀트 종목들의 자산 배분 비중을 최적화하고, 시장 벤치마크 대비 성과 시뮬레이션을 진행합니다.")

# 1. Retrieve screened tickers and market from session state
screened_tickers = st.session_state.get('screened_tickers', [])
screened_names = st.session_state.get('screened_names', [])
market_code = st.session_state.get('screened_market', 'KOR')

prefix = "kor" if market_code == "KOR" else "global"

# Fallback to first 20 tickers if empty
if not screened_tickers:
    try:
        df_raw = calculate_dynamic_qvm(market=market_code)
        if not df_raw.empty:
            screened_tickers = df_raw.head(20)['종목코드'].tolist()
            screened_names = df_raw.head(20)['종목명'].tolist()
            st.session_state['screened_tickers'] = screened_tickers
            st.session_state['screened_names'] = screened_names
    except Exception:
        pass

if not screened_tickers:
    st.warning("⚠️ 스크리닝된 종목이 없습니다. '2_Screening' 페이지에서 종목을 먼저 골라주세요.")
else:
    # Selected stocks summary
    st.markdown("<div class='citrus-card'>", unsafe_allow_html=True)
    st.markdown(f"### 📋 대상 포트폴리오 종목 ({len(screened_tickers)}개 / 시장: {market_code})")
    st.write(", ".join([f"{name}({code})" for name, code in zip(screened_names, screened_tickers)]))
    st.markdown("</div>", unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown("<div class='citrus-card'>", unsafe_allow_html=True)
        st.markdown("### ⚙️ 최적화 및 시뮬레이션 설정")
        
        opt_method = st.selectbox(
            "자산 배분 최적화 방식",
            options=["MaxSharpe (최대 샤프 지수)", "MinRisk (최소 위험)"]
        )
        method_code = 'MaxSharpe' if "MaxSharpe" in opt_method else 'MinRisk'
        
        st.markdown("---")
        st.markdown("##### 🔄 백테스트 리밸런싱 사양 (Ch 16)")
        rebal_freq = st.selectbox(
            "포트폴리오 리밸런싱 주기",
            options=["Buy & Hold (단순 보유)", "Monthly Rebalancing (매월)", "Quarterly Rebalancing (분기별)"]
        )
        
        fee_pct = st.slider(
            "편도 거래 비용 & 슬리피지 비율 (%)",
            min_value=0.0, max_value=2.0, value=0.25, step=0.05
        )
        fee_ratio = fee_pct / 100.0
        
        # Trigger Optimization
        st.markdown("---")
        run_opt = st.button("🚀 포트폴리오 최적화 및 백테스트 시작", use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
        
    if run_opt or 'optimized_weights' in st.session_state:
        # Check if user clicked or loading from session state
        # If parameters changed, force re-run
        params_key = f"{method_code}_{rebal_freq}_{fee_pct}_{market_code}"
        
        if run_opt or st.session_state.get('backtest_params_key') != params_key:
            with st.spinner("Riskfolio 최적 비중 연산 및 백테스팅 진행 중..."):
                weights = optimize_portfolio(screened_tickers, method=method_code, market=market_code)
                st.session_state['optimized_weights'] = weights
                
                # Run Backtest
                df_backtest, p_cagr, p_mdd, b_cagr, b_mdd = run_backtest(
                    screened_tickers, weights, market=market_code, 
                    rebalance_freq=rebal_freq, fee_ratio=fee_ratio
                )
                st.session_state['backtest_df'] = df_backtest
                st.session_state['backtest_metrics'] = (p_cagr, p_mdd, b_cagr, b_mdd)
                st.session_state['backtest_params_key'] = params_key
        else:
            weights = st.session_state['optimized_weights']
            df_backtest = st.session_state['backtest_df']
            p_cagr, p_mdd, b_cagr, b_mdd = st.session_state['backtest_metrics']
            
        # Display Optimization Results
        if weights:
            name_map = dict(zip(screened_tickers, screened_names))
            df_weights = pd.DataFrame([
                {"종목명": name_map.get(code, code), "가중치": w} 
                for code, w in weights.items() if w > 0.001
            ]).sort_values("가중치", ascending=False)
            
            with col2:
                st.markdown("<div class='citrus-card'>", unsafe_allow_html=True)
                st.markdown("### 🍩 최적 자산 배분 비중")
                fig_weights = px.pie(
                    df_weights,
                    names="종목명",
                    values="가중치",
                    hole=0.4,
                    color_discrete_sequence=px.colors.qualitative.Pastel,
                    title="선택한 종목 자산배분 최적화 가중치"
                )
                st.plotly_chart(fig_weights, use_container_width=True)
                st.markdown("</div>", unsafe_allow_html=True)
                
            # Backtesting Chart and Metrics
            if not df_backtest.empty:
                st.markdown("<div class='citrus-card'>", unsafe_allow_html=True)
                st.markdown("### 📊 과거 1개년 누적 수익률 백테스트 결과")
                
                # KPIs Table
                kcol1, kcol2, kcol3, kcol4 = st.columns(4)
                kcol1.metric("포트폴리오 CAGR", f"{p_cagr}%")
                kcol2.metric("포트폴리오 MDD", f"{p_mdd}%")
                kcol3.metric("벤치마크 CAGR", f"{b_cagr}%")
                kcol4.metric("벤치마크 MDD", f"{b_mdd}%")
                
                st.markdown("---")
                
                # Line chart
                fig_line = px.line(
                    df_backtest,
                    x="날짜",
                    y=["Portfolio", "Benchmark"],
                    labels={"value": "누적 수익률 (%)", "variable": "구분"},
                    title="포트폴리오 vs 벤치마크 누적 수익률 흐름"
                )
                fig_line.update_layout(
                    legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01),
                    hovermode="x unified"
                )
                st.plotly_chart(fig_line, use_container_width=True)
                st.markdown("</div>", unsafe_allow_html=True)
                
                # Ch 17 - Order Signals Sheet Panel
                st.markdown("<div class='citrus-card'>", unsafe_allow_html=True)
                st.markdown("### 📋 증권사 주문 자동 생성 시트 (Ch 17 연동)")
                st.markdown("QVM 최적화 포트폴리오를 기반으로 총 투자자금 대비 가상의 매수/매도 주문 수량을 생성합니다.")
                
                default_cap = 10000000 if market_code == "KOR" else 100000
                cap_label = "총 투자 자금 (원)" if market_code == "KOR" else "총 투자 자금 (달러)"
                
                capital = st.number_input(cap_label, min_value=1000, value=default_cap, step=100000 if market_code=="KOR" else 1000)
                
                df_orders = generate_order_signals(screened_tickers, weights, capital=capital, market=market_code)
                
                if not df_orders.empty:
                    st.dataframe(df_orders, use_container_width=True)
                    
                    # CSV download button (utf-8-sig for Excel compatibility)
                    csv_data = df_orders.to_csv(index=False).encode('utf-8-sig')
                    st.download_button(
                        label="📥 증권사 API 주문용 CSV 다운로드",
                        data=csv_data,
                        file_name=f"citrus_order_signals_{market_code}.csv",
                        mime="text/csv"
                    )
                else:
                    st.info("주문 수량을 산출할 수 없습니다.")
                st.markdown("</div>", unsafe_allow_html=True)
                
            else:
                st.error("백테스팅 연산 중 오류가 발생했거나 주가 데이터가 존재하지 않습니다.")

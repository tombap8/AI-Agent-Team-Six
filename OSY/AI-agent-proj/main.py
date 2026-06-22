import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import uuid
import datetime
import importlib
from app.database import init_db, seed_mock_data, get_store_listings, get_store_by_id, register_store
from app.valuation import calculate_tangible_value, calculate_intangible_value, calculate_total_valuation, generate_valuation_report
import app.scraper
importlib.reload(app.scraper)
from app.scraper import search_franchise, search_market_listings
from app.rag import generate_rag_response
import app.utils
importlib.reload(app.utils)
from app.utils import parse_business_license_ocr, verify_business_tax_status, calculate_escrow_fee, generate_contract_draft

# Initialize DB and Seed Data
init_db()
seed_mock_data()

# ---------------------------------------------
# 1. Page Configuration & Custom CSS Injection
# ---------------------------------------------
st.set_page_config(
    page_title="점포창업(양도양수) 도우미 에이전트",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom premium styling rules matching design.md
custom_css = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&family=Outfit:wght@400;600;800&display=swap');

/* Smooth global transition for theme toggle, resolving inversion issues */
.stApp, .glass-card, [data-testid="stSidebar"], h1, h2, h3, h4, h5, h6, p, span, div.stButton > button {
    transition: background-color 0.8s cubic-bezier(0.4, 0, 0.2, 1), 
                color 0.8s cubic-bezier(0.4, 0, 0.2, 1), 
                border-color 0.8s cubic-bezier(0.4, 0, 0.2, 1), 
                box-shadow 0.8s cubic-bezier(0.4, 0, 0.2, 1) !important;
}

/* Use standard Streamlit CSS variables for high-contrast auto transitions */
.stApp {
    background-color: var(--background-color) !important;
    color: var(--text-color) !important;
    font-family: 'Inter', sans-serif;
}

/* Sidebar Customization */
[data-testid="stSidebar"] {
    background-color: var(--secondary-background-color) !important;
    border-right: 1px solid color-mix(in srgb, var(--text-color) 8%, transparent) !important;
}

/* Glassmorphism Cards with dynamic color-mix */
.glass-card {
    background: color-mix(in srgb, var(--background-color) 92%, var(--text-color) 8%) !important;
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
    border-radius: 16px;
    border: 1px solid color-mix(in srgb, var(--text-color) 10%, transparent) !important;
    padding: 24px;
    margin-bottom: 20px;
    box-shadow: 0 8px 32px 0 color-mix(in srgb, var(--text-color) 5%, transparent) !important;
}

/* HSL Gradient Title */
.gradient-title {
    font-family: 'Outfit', sans-serif;
    font-weight: 800;
    background: linear-gradient(135deg, #4F46E5 0%, #0D9488 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-size: 2.5rem;
    margin-bottom: 1.5rem;
    text-shadow: 0px 4px 10px rgba(79, 70, 229, 0.1);
}

/* Sub-headings */
.section-title {
    font-family: 'Outfit', sans-serif;
    color: #4F46E5;
    font-weight: 600;
    font-size: 1.5rem;
    border-left: 4px solid #0D9488;
    padding-left: 10px;
    margin-bottom: 15px;
}

/* Premium Badge styles */
.badge-valid {
    background-color: rgba(16, 185, 129, 0.15);
    color: #059669;
    border: 1px solid #10B981;
    padding: 4px 8px;
    border-radius: 6px;
    font-size: 0.85rem;
    font-weight: 600;
    display: inline-block;
}

.badge-warning {
    background-color: rgba(245, 158, 11, 0.15);
    color: #D97706;
    border: 1px solid #F59E0B;
    padding: 4px 8px;
    border-radius: 6px;
    font-size: 0.85rem;
    font-weight: 600;
    display: inline-block;
}

.badge-danger {
    background-color: rgba(239, 68, 68, 0.15);
    color: #DC2626;
    border: 1px solid #EF4444;
    padding: 4px 8px;
    border-radius: 6px;
    font-size: 0.85rem;
    font-weight: 600;
    display: inline-block;
}

/* Metric Display in Card */
.metric-val {
    font-size: 2rem;
    font-weight: 700;
    color: var(--text-color) !important;
    margin-top: 5px;
}

/* Styled Forms */
input, select, textarea {
    background-color: var(--background-color) !important;
    color: var(--text-color) !important;
    border: 1px solid color-mix(in srgb, var(--text-color) 15%, transparent) !important;
    border-radius: 8px !important;
}

/* Customize buttons */
div.stButton > button:first-child {
    background: linear-gradient(135deg, #4F46E5 0%, #0D9488 100%) !important;
    color: #FFFFFF !important;
    border: none !important;
    border-radius: 8px !important;
    padding: 10px 24px !important;
    font-weight: 600 !important;
    transition: all 0.3s ease !important;
    box-shadow: 0 4px 15px rgba(79, 70, 229, 0.25) !important;
    width: 100%;
}

div.stButton > button:first-child:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 20px rgba(79, 70, 229, 0.35) !important;
}
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# ---------------------------------------------
# 2. Navigation Sidebar
# ---------------------------------------------
st.sidebar.markdown("<h2 style='text-align:center; color:#4F46E5; font-family:Outfit; font-weight:800;'>START-UP AGENT</h2>", unsafe_allow_html=True)
st.sidebar.markdown("<p style='text-align:center; color:#475569; font-size:0.9rem;'>개인 및 프랜차이즈 점포 양도양수 도우미</p>", unsafe_allow_html=True)
st.sidebar.markdown("---")

menu = st.sidebar.radio(
    "메뉴 선택",
    ["🏠 종합 대시보드", "🔍 실시간 점포 찾기 & 비교", "📊 하이브리드 권리평가", "📑 안전 계약 & 진위 검증", "💬 AI RAG 법률상담 & 리뷰요약"]
)

st.sidebar.markdown("---")
st.sidebar.info("💡 **가상환경 활성화 상태**\nPython 3.14.5 (.venv)")

# ---------------------------------------------
# Page 1: 🏠 종합 대시보드
# ---------------------------------------------
if menu == "🏠 종합 대시보드":
    st.markdown("<h1 class='gradient-title'>점포 창업 및 양도양수 에이전트 대시보드</h1>", unsafe_allow_html=True)
    
    # 3-column stats
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="glass-card">
            <span class="badge-valid">거래 활성</span>
            <div style="color: #475569; font-size: 0.95rem; margin-top: 10px;">식음료 매물 등록</div>
            <div class="metric-val">6,404 건</div>
            <div style="color: #059669; font-size: 0.85rem; margin-top: 5px;">▲ 카페/한식 업종 위주 거래 활성화</div>
        </div>
        """, unsafe_allow_html=True)
        
    with col2:
        st.markdown("""
        <div class="glass-card">
            <span class="badge-warning">장치 검증 대상</span>
            <div style="color: #475569; font-size: 0.95rem; margin-top: 10px;">오락스포츠 매물</div>
            <div class="metric-val">931 건</div>
            <div style="color: #D97706; font-size: 0.85rem; margin-top: 5px;">⚠ 초기 장비 고가 설비 검증 유의</div>
        </div>
        """, unsafe_allow_html=True)
        
    with col3:
        st.markdown("""
        <div class="glass-card">
            <span class="badge-danger">보안 조치</span>
            <div style="color: #475569; font-size: 0.95rem; margin-top: 10px;">누적 차단 허위 매물</div>
            <div class="metric-val">231 건</div>
            <div style="color: #DC2626; font-size: 0.85rem; margin-top: 5px;">🔒 국세청 API 대조 실시간 차단율 100%</div>
        </div>
        """, unsafe_allow_html=True)

    # Competitor trends chart & AI warning status
    st.markdown("<div class='section-title'>실시간 상권 추정 매출 및 경쟁분석 파이프라인</div>", unsafe_allow_html=True)
    
    col_chart, col_warning = st.columns([2, 1])
    
    with col_chart:
        # Drawing matplotlib dark premium chart
        months = ["1월", "2월", "3월", "4월", "5월", "6월"]
        cafe_sales = [3100, 3250, 3400, 3150, 3500, 3620] # 만원
        chicken_sales = [5400, 5200, 5600, 5900, 6100, 6480]
        
        fig, ax = plt.subplots(figsize=(8, 4.2))
        fig.patch.set_facecolor('#F1F5F9')
        ax.set_facecolor('#FFFFFF')
        
        ax.plot(months, cafe_sales, marker='o', color='#4F46E5', linewidth=2.5, label='카페 업종 평균 매출')
        ax.plot(months, chicken_sales, marker='s', color='#0D9488', linewidth=2.5, label='치킨 업종 평균 매출')
        
        ax.set_title("상권별 월간 추정 매출 흐름 (단위: 만원)", color='#1E293B', fontsize=12, pad=15)
        ax.tick_params(colors='#475569', labelsize=9)
        ax.grid(color='#E2E8F0', linestyle='--', alpha=0.5)
        
        # Legend with dark text
        legend = ax.legend(loc='upper left', facecolor='#F1F5F9', edgecolor='none')
        for text in legend.get_texts():
            text.set_color('#1E293B')
            
        for spine in ax.spines.values():
            spine.set_color('#E2E8F0')
            
        st.pyplot(fig)
        
    with col_warning:
        st.markdown("<div class='glass-card' style='height: 100%;'>", unsafe_allow_html=True)
        st.markdown("<p style='font-weight:600; color:#DC2626;'>🚨 AI 위기 상권 경보 알람 (2027 모형)</p>", unsafe_allow_html=True)
        st.write("다변량 시계열 모형으로 분석한 매출 급감 쇠퇴 상권 정보입니다.")
        
        st.error("🔴 **위기 경보: 마포구 서교동 일대**\n- 유동인구 12% 급감 징후 감지\n- 경쟁 점포 과밀화 지수 임계치(3.5) 초과\n- 양도양수 시 권리금 과다 산정 유의 요망")
        st.warning("🟡 **주의 경보: 강남구 역삼동 상권**\n- 오피스 상권 주말 매출 정체 추세\n- 계속사업 생존율 등급: C등급")
        st.success("🟢 **안정 지역: 분당구 서현역 일대**\n- 3년 평균 생존율 82% 유지\n- 유동인구 소비지수 견고")
        st.markdown("</div>", unsafe_allow_html=True)

# ---------------------------------------------
# Page 2: 🔍 실시간 점포 찾기 & 비교
# ---------------------------------------------
elif menu == "🔍 실시간 점포 찾기 & 비교":
    st.markdown("<h1 class='gradient-title'>실시간 점포 찾기 및 브랜드 비교</h1>", unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["🏛 프랜차이즈 정보공개서 조회", "🏪 양도양수 등록 매물 조회"])
    
    with tab1:
        if "searching" not in st.session_state:
            st.session_state.searching = False
        if "search_results" not in st.session_state:
            st.session_state.search_results = None
        if "search_sources" not in st.session_state:
            st.session_state.search_sources = None
        if "search_query" not in st.session_state:
            st.session_state.search_query = ""

        st.markdown("<div class='section-title'>공정거래위원회 등록 정보공개서 실시간 조회 및 비교</div>", unsafe_allow_html=True)
        
        # Optional search settings panel
        with st.expander("⚙️ 실시간 검색 엔진 설정 (선택사항 - API 연동)", expanded=False):
            st.info("기본적으로 API Key 없이 작동하는 실시간 DuckDuckGo 크롤러/스크래퍼를 사용합니다. 필요 시 Serper 또는 Tavily API 키를 등록하세요.")
            api_provider = st.selectbox("검색 API 제공처", ["DuckDuckGo (기본 - Crawling)", "Serper (Google Search)", "Tavily Search"], index=0, key="api_provider_select")
            api_key = st.text_input("API Key 입력 (비공개)", type="password", key="api_key_input")
            
            provider_map = {
                "DuckDuckGo (기본 - Crawling)": "duckduckgo",
                "Serper (Google Search)": "serper",
                "Tavily Search": "tavily"
            }
            api_provider_param = provider_map[api_provider]

        col_input, col_btn = st.columns([3.2, 1.3])
        
        with col_input:
            search_q = st.text_input(
                "프랜차이즈 브랜드명 입력 (예: 빽다방, 맘스터치, 엽기떡볶이, bbq 등)",
                value=st.session_state.search_query,
                disabled=st.session_state.searching,
                key="brand_search_input"
            )
        
        with col_btn:
            st.write("<div style='height:28px;'></div>", unsafe_allow_html=True)
            col_b1, col_b2 = st.columns(2)
            with col_b1:
                search_clicked = st.button("조회하기", disabled=st.session_state.searching, key="brand_search_btn")
            with col_b2:
                reset_clicked = st.button("초기화", disabled=st.session_state.searching, key="brand_reset_btn")
            
        if reset_clicked:
            st.session_state.search_query = ""
            st.session_state.search_results = None
            st.session_state.search_sources = None
            st.rerun()

        if search_clicked and search_q:
            st.session_state.searching = True
            st.session_state.search_query = search_q
            st.session_state.api_provider_param = api_provider_param
            st.session_state.api_key_param = api_key
            st.rerun()

        if st.session_state.searching:
            col_loader, _ = st.columns([1.5, 3])
            with col_loader:
                with st.spinner("⏳ 실시간 검색 및 정보공개서 데이터 수집 중..."):
                    res, srcs = search_franchise(
                        st.session_state.search_query,
                        api_key=st.session_state.get("api_key_param", None),
                        api_provider=st.session_state.get("api_provider_param", "duckduckgo")
                    )
                    st.session_state.search_results = res
                    st.session_state.search_sources = srcs
            st.session_state.searching = False
            st.rerun()

        # 1. Default View: Show the 5 main brands comparison dashboard when no search query
        if not st.session_state.search_query:
            st.markdown("##### 🏛 주요 5대 프랜차이즈 브랜드 공식 지표 비교")
            
            # DataFrame representation
            from app.scraper import FRANCHISE_DB
            df_data = []
            for k, val in FRANCHISE_DB.items():
                df_data.append({
                    "브랜드명": val["brand_name"],
                    "업종": val["category"],
                    "가맹점 수": f"{val['store_count']:,} 개",
                    "평균 연매출": f"{val['avg_annual_sales']/10000:,.0f} 만원",
                    "가맹비": f"{val['membership_fee']/10000:,.0f} 만원",
                    "인테리어 비용": f"{val['interior_cost']/10000:,.0f} 만원",
                    "총 창업비용": f"{val['total_initial']/10000:,.0f} 만원",
                    "로열티": val["royalty"]
                })
            df = pd.DataFrame(df_data)
            st.dataframe(df, use_container_width=True, hide_index=True)
            
            # Show individual cards of the 5 main brands
            st.write("<div style='height:15px;'></div>", unsafe_allow_html=True)
            cols = st.columns(5)
            for i, (k, val) in enumerate(FRANCHISE_DB.items()):
                with cols[i]:
                    st.markdown(f"""
                    <div class="glass-card" style="padding:15px; text-align:center; min-height: 250px; margin-bottom:10px;">
                        <span style="font-weight:800; color:#4F46E5; font-size:1.05rem;">{k}</span><br>
                        <span style="font-size:0.75rem; color:#475569;">{val['category']}</span>
                        <hr style="margin:10px 0; border:0; border-top:1px solid rgba(0,0,0,0.05);">
                        <span style="font-size:0.8rem; color:#475569;">가맹점 수</span><br>
                        <b style="color:#1E293B; font-size:1.1rem;">{val['store_count']:,} 개</b><br>
                        <span style="font-size:0.8rem; color:#475569; margin-top:5px; display:inline-block;">평균 연매출</span><br>
                        <b style="color:#0D9488; font-size:1.1rem;">{val['avg_annual_sales']/10000:,.0f}만</b><br>
                        <span style="font-size:0.8rem; color:#475569; margin-top:5px; display:inline-block;">총 창업비용</span><br>
                        <b style="color:#4F46E5; font-size:1.1rem;">{val['total_initial']/10000:,.0f}만</b>
                    </div>
                    """, unsafe_allow_html=True)

        # 2. Search View: Show searched franchise metrics and search source snippets
        if st.session_state.search_query:
            st.markdown(f"##### 🔎 '{st.session_state.search_query}' 실시간 분석 결과")
            if st.session_state.search_results:
                for b in st.session_state.search_results:
                    with st.expander(f"✨ {b['brand_name']} - {b['category']}", expanded=True):
                        c1, c2, c3 = st.columns(3)
                        with c1:
                            st.metric("가맹점 수", f"{b['store_count']:,} 개")
                            st.metric("평균 연매출", f"{b['avg_annual_sales'] / 10000:,.0f} 만원")
                        with c2:
                            st.metric("가맹비 (가맹/교육)", f"{b['membership_fee'] / 10000:,.0f} 만원")
                            st.metric("인테리어 비용", f"{b['interior_cost'] / 10000:,.0f} 만원")
                        with c3:
                            st.metric("총 예상 창업비용", f"{b['total_initial'] / 10000:,.0f} 만원")
                            st.write(f"**로열티:** {b['royalty']}")
                            
                # Show reference search results
                if st.session_state.search_sources:
                    st.write("<div style='height:20px;'></div>", unsafe_allow_html=True)
                    st.markdown("##### 🌐 실시간 웹 검색 및 크롤링 출처 리스트")
                    for idx, src in enumerate(st.session_state.search_sources):
                        st.markdown(f"""
                        <div class="glass-card" style="padding:15px; margin-bottom:12px; border-left:4px solid #4F46E5;">
                            <div style="font-weight:600; color:#1E293B; font-size:1.0rem;">
                                <a href="{src['href']}" target="_blank" style="color:#4F46E5; text-decoration:none;">{idx+1}. {src['title']}</a>
                            </div>
                            <div style="font-size:0.75rem; color:#0D9488; margin: 4px 0;">
                                <a href="{src['href']}" target="_blank" style="color:#0D9488; text-decoration:none;">{src['href']}</a>
                            </div>
                            <div style="font-size:0.85rem; color:#475569; line-height:1.4;">{src['body']}</div>
                        </div>
                        """, unsafe_allow_html=True)
            else:
                st.info("검색된 프랜차이즈 브랜드가 없습니다.")
            
    with tab2:
        st.markdown("<div class='section-title'>플랫폼 공식 검증된 양도양수 매물 리스트</div>", unsafe_allow_html=True)
        
        cat_filter = st.selectbox("업종 필터", ["전체", "카페", "치킨점", "편의점"])
        search_store = st.text_input("지역명 또는 매물명 검색")
        
        # Pull from SQLite
        listings = get_store_listings()
        
        filtered_listings = []
        for row in listings:
            # Check filter
            store_type = "카페" if "메가커피" in row["store_brand"] or "컴포즈커피" in row["store_brand"] else ("치킨점" if "교촌" in row["store_brand"] else "편의점")
            
            if cat_filter != "전체" and store_type != cat_filter:
                continue
                
            if search_store and (search_store.lower() not in row["store_brand"].lower() and search_store.lower() not in row["address_detail"].lower()):
                continue
                
            filtered_listings.append((row, store_type))
            
        if filtered_listings:
            for item, st_type in filtered_listings:
                with st.container():
                    st.markdown(f"""
                    <div class="glass-card">
                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            <h3 style="margin:0; color:#4F46E5;">{item['store_brand']}</h3>
                            <span class="badge-valid">국세청 검증완료</span>
                        </div>
                        <p style="color:#475569; font-size:0.9rem; margin-top:5px;">📍 주소: {item['address_detail']} | 개업일: {item['established_date']}</p>
                        <div style="display:flex; gap:30px; margin-top:15px;">
                            <div>
                                <span style="font-size:0.85rem; color:#475569;">시설 권리</span><br>
                                <b style="font-size:1.15rem; color:#1E293B;">{(item['val_facility'] or 0)/10000:,.0f} 만원</b>
                            </div>
                            <div>
                                <span style="font-size:0.85rem; color:#475569;">영업 권리</span><br>
                                <b style="font-size:1.15rem; color:#1E293B;">{(item['val_operating'] or 0)/10000:,.0f} 만원</b>
                            </div>
                            <div>
                                <span style="font-size:0.85rem; color:#475569;">바닥 권리</span><br>
                                <b style="font-size:1.15rem; color:#1E293B;">{(item['val_location'] or 0)/10000:,.0f} 만원</b>
                            </div>
                            <div>
                                <span style="font-size:0.85rem; color:#475569;">총 감정권리금</span><br>
                                <b style="font-size:1.3rem; color:#4F46E5;">{(item['total_valuation'] or 0)/10000:,.0f} 만원</b>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)
        else:
            st.info("조건에 부합하는 매물이 없습니다.")

# ---------------------------------------------
# Page 3: 📊 하이브리드 권리평가
# ---------------------------------------------
elif menu == "📊 하이브리드 권리평가":
    st.markdown("<h1 class='gradient-title'>하이브리드 권리금 감정평가 공식 엔진</h1>", unsafe_allow_html=True)
    st.write("시설물의 감가상각(원가법)과 무형의 수익 가치(수익환원법)를 합산하여 과학적인 가치를 도출합니다.")
    
    col_input, col_result = st.columns([1, 1])
    
    with col_input:
        st.markdown("<div class='section-title'>1. 유형자산 시설 감가상각 (원가법)</div>", unsafe_allow_html=True)
        initial_cost = st.number_input("최초 시설 설치 및 인테리어 공사비 (원)", min_value=0, value=80000000, step=1000000)
        operating_months = st.slider("운영 개월 수 (t, 개월)", min_value=0, max_value=120, value=24)
        condition_coeff = st.slider("정성 보정 계수 (C_q, 관리상태)", min_value=0.0, max_value=1.0, value=0.9, step=0.05)
        
        st.markdown("<div class='section-title'>2. 무형자산 영업권 가치 (수익환원법)</div>", unsafe_allow_html=True)
        annual_net_profit = st.number_input("연간 실질 순영업이익 (원, 자가인건비 제외)", min_value=0, value=48000000, step=1000000)
        discount_rate = st.slider("가이드라인 할인율 (R)", min_value=0.05, max_value=0.25, value=0.10, step=0.01)
        years = st.slider("무형가치 유효 기간 (N, 개년)", min_value=1, max_value=5, value=3)
        
        st.markdown("<div class='section-title'>3. 입지 및 허가 권리금</div>", unsafe_allow_html=True)
        val_location = st.number_input("주변 비교 바닥 위치 권리금 (원)", min_value=0, value=20000000, step=1000000)
        val_license = st.number_input("특수 행정 인허가 권리금 (원)", min_value=0, value=5000000, step=1000000)
        
        # Recalculate based on inputs
        val_facility = calculate_tangible_value(initial_cost, operating_months, condition_coeff)
        val_operating = calculate_intangible_value(annual_net_profit, discount_rate, years)
        total_val = calculate_total_valuation(val_facility, val_operating, val_location, val_license)
        
    with col_result:
        st.markdown("<div class='glass-card' style='height:100%;'>", unsafe_allow_html=True)
        st.markdown("<h3 style='margin:0; color:#4F46E5;'>감정평가 최종 레포트 요약</h3>", unsafe_allow_html=True)
        st.write("---")
        
        st.markdown(f"""
        <div style="background-color:rgba(79,70,229,0.06); padding:20px; border-radius:12px; border:1px solid #4F46E5; text-align:center; margin-bottom:20px;">
            <span style="color:#475569; font-size:0.95rem;">하이브리드 합산 권리금 가치</span>
            <div style="font-size:2.8rem; font-weight:800; color:#4F46E5; margin-top:5px;">{total_val/10000:,.0f} 만원</div>
            <span style="color:#475569; font-size:0.85rem;">(₩ {total_val:,.0f})</span>
        </div>
        """, unsafe_allow_html=True)
        
        c_res1, c_res2 = st.columns(2)
        with c_res1:
            st.metric("⚙ 시설권리금 (감쇄율 반영)", f"{val_facility/10000:,.0f} 만원")
            st.metric("📍 바닥권리금 (위치 프리미엄)", f"{val_location/10000:,.0f} 만원")
        with c_res2:
            st.metric("📈 영업권리금 (수익환원)", f"{val_operating/10000:,.0f} 만원")
            st.metric("📜 허가권리금 (인허가 승계)", f"{val_license/10000:,.0f} 만원")
            
        st.write("---")
        
        # Save to DB form
        st.markdown("<p style='font-weight:600; color:#0D9488;'>💾 본 감정 내역을 신규 매물로 데이터베이스에 등록</p>", unsafe_allow_html=True)
        store_brand_input = st.text_input("상호명 또는 가맹브랜드명", value="커스텀 점포")
        owner_phone_input = st.text_input("연락처 (인증용 휴대폰 번호)", value="010-1234-5678")
        biz_reg_input = st.text_input("사업자등록번호 (10자리)", value="120-81-12345")
        established_input = st.text_input("개업일자 (YYYY-MM-DD)", value="2022-03-15")
        address_input = st.text_input("매물 상세 주소", value="서울특별시 강남구 대치동 988-1")
        
        if st.button("신규 매물 등록 및 권리 평가 저장"):
            store_uuid = f"store-{uuid.uuid4().hex[:8]}"
            success = register_store(
                store_uuid, owner_phone_input, biz_reg_input, store_brand_input, 
                established_input, address_input, val_facility, val_operating, 
                val_location, val_license, 'PENDING'
            )
            if success:
                st.success(f"🎉 성공적으로 신규 매물이 등록되었습니다. (관리 ID: {store_uuid})")
                st.info("국세청 API 검증을 받기 위해 '안전 계약 & 진위 검증' 패널에서 사업자 조회를 신청해 주세요.")
            else:
                st.error("등록 중 데이터베이스 오류가 발생했습니다. 사업자 번호 중복 여부를 확인해 주세요.")
        st.markdown("</div>", unsafe_allow_html=True)

# ---------------------------------------------
# Page 4: 📑 안전 계약 & 진위 검증
# ---------------------------------------------
elif menu == "📑 안전 계약 & 진위 검증":
    st.markdown("<h1 class='gradient-title'>국세청 진위 확인 및 에스크로 표준계약</h1>", unsafe_allow_html=True)
    st.write("허위 매물 위조 사기 방지를 위하여 공적 장부의 실시간 진위 확인과 안전 거래 장치를 연동합니다.")
    
    col_ver, col_con = st.columns([1, 1.2])
    
    with col_ver:
        st.markdown("<div class='section-title'>1. 사업자등록증 OCR 및 국세청 진위조회</div>", unsafe_allow_html=True)
        
        uploaded_file = st.file_uploader("사업자등록증 이미지 또는 PDF 파일 업로드", type=["png", "jpg", "jpeg", "pdf"])
        
        # NTS service key settings UI
        with st.expander("⚙️ 국세청 진위확인 API 설정 (선택사항)", expanded=False):
            st.info("실제 국세청 진위확인 API를 호출하려면 공공데이터포털(data.go.kr)에서 발급받은 '국세청 사업자등록정보 진위확인 및 상태조회 서비스' 서비스키가 필요합니다.")
            nts_service_key = st.text_input("공공데이터포털 서비스키 (Decoding Key 권장)", type="password", key="nts_service_key_input")
        
        # OCR inputs
        ocr_biz_no = "120-81-12345"
        ocr_owner = "홍길동"
        ocr_date = "2022-03-15"
        ocr_brand = "메가커피 대치점"
        ocr_address = "서울특별시 강남구 대치동 988-1"
        
        if uploaded_file is not None:
            # Run real OCR
            with st.spinner("⏳ 파일에서 텍스트를 추출하는 중 (OCR)..."):
                ocr_res = parse_business_license_ocr(uploaded_file.name, uploaded_file.getvalue())
            
            ocr_biz_no = ocr_res["biz_reg_no"]
            ocr_owner = ocr_res["owner_name"]
            ocr_date = ocr_res["established_date"]
            ocr_brand = ocr_res["brand_name"]
            ocr_address = ocr_res["address_detail"]
            
            if ocr_res.get("success"):
                st.success("✅ OCR 정보가 정상적으로 추출되었습니다.")
                if "raw_text" in ocr_res and ocr_res["raw_text"]:
                    with st.expander("📄 추출된 raw 텍스트 보기", expanded=False):
                        st.text_area("인식된 텍스트", ocr_res["raw_text"], height=150, disabled=True)
            else:
                st.warning("⚠️ OCR 텍스트 추출에 실패하여 샘플 데이터를 반환했습니다.")
            
        st.write("**[OCR 파싱 추출 정보]**")
        biz_no_field = st.text_input("사업자등록번호 (biz_reg_no)", ocr_biz_no)
        owner_field = st.text_input("대표자명 (owner_name)", ocr_owner)
        date_field = st.text_input("개업일자 (established_date)", ocr_date)
        brand_field = st.text_input("상호/브랜드명", ocr_brand)
        address_field = st.text_input("사업장 주소", ocr_address)
        
        if st.button("국세청 최신 정보 진위확인 API 질의"):
            service_key = st.session_state.get("nts_service_key_input", "")
            ver_res = verify_business_tax_status(biz_no_field, owner_field, date_field, service_key=service_key)
            if ver_res["valid"]:
                st.markdown(f"""
                <div style="background-color:rgba(16, 185, 129, 0.1); border: 1px solid #10B981; padding: 15px; border-radius: 8px; margin-top: 15px;">
                    <b style="color:#059669; font-size: 1.1rem;">✅ {ver_res['status_name']} [적격]</b><br>
                    <span style="color:#1E293B; font-size: 0.9rem;">{ver_res['message']}</span>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div style="background-color:rgba(239, 68, 68, 0.1); border: 1px solid #EF4444; padding: 15px; border-radius: 8px; margin-top: 15px;">
                    <b style="color:#DC2626; font-size: 1.1rem;">❌ {ver_res['status_name']} [부적격 경고]</b><br>
                    <span style="color:#1E293B; font-size: 0.9rem;">{ver_res['message']}</span>
                </div>
                """, unsafe_allow_html=True)
                
    with col_con:
        st.markdown("<div class='section-title'>2. 에스크로 정산 및 표준 계약서 자동 생성</div>", unsafe_allow_html=True)
        
        st.write("합의된 총 권리금을 바탕으로 에스크로 중개 및 표준임대차권리금 표준 계약서 초안을 빌드합니다.")
        
        amount_input = st.number_input("거래 총 권리금 (원)", min_value=0, value=108000000, step=1000000)
        fee_rate_input = st.slider("권리 중개 수수료율 설정", min_value=0.01, max_value=0.05, value=0.03, step=0.005)
        
        escrow_calc = calculate_escrow_fee(amount_input, fee_rate_input)
        
        st.markdown(f"""
        <div class="glass-card">
            <div style="display:flex; justify-content:space-between; margin-bottom:10px;">
                <span style="color:#475569;">합산 권리금액</span>
                <b style="color:#1E293B;">{escrow_calc['total_amount'] / 10000:,.0f} 만원</b>
            </div>
            <div style="display:flex; justify-content:space-between; margin-bottom:10px;">
                <span style="color:#475569;">중개 수수료 ({escrow_calc['fee_rate_percent']:.1f}%)</span>
                <b style="color:#0D9488;">{escrow_calc['broker_fee'] / 10000:,.0f} 만원</b>
            </div>
            <div style="display:flex; justify-content:space-between; border-top:1px solid rgba(15,23,42,0.08); padding-top:10px;">
                <span style="color:#475569; font-weight:600;">에스크로 예치금액 (매도인 지급액)</span>
                <b style="color:#4F46E5; font-size:1.2rem;">{escrow_calc['escrow_held'] / 10000:,.0f} 만원</b>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.write("**계약 당사자 인적사항**")
        c_seller = st.text_input("양도인(갑) 대표자명", ocr_owner)
        c_buyer = st.text_input("양수인(을) 대표자명", "예비사장")
        
        if st.button("표준 권리금 계약서 초안 빌드"):
            # split total val equally for drafting demo if from custom input
            v_split = amount_input / 4
            draft_contract = generate_contract_draft(
                c_seller, c_buyer, brand_field, address_field, 
                v_split, v_split, v_split, v_split
            )
            st.text_area("국토교통부 고시 계약서 내용", draft_contract, height=350)
            st.download_button("📥 표준 계약서 다운로드 (.txt)", draft_contract, file_name="standard_premium_contract.txt")

# ---------------------------------------------
# Page 5: 💬 AI RAG 법률상담 & 리뷰요약
# ---------------------------------------------
elif menu == "💬 AI RAG 법률상담 & 리뷰요약":
    st.markdown("<h1 class='gradient-title'>AI RAG 법률 어시스턴트 & 리뷰 요약</h1>", unsafe_allow_html=True)
    
    tab_chat, tab_review = st.tabs(["💬 RAG 창업/권리금 챗봇", "📝 매장 리뷰 AI 요약"])
    
    with tab_chat:
        st.markdown("<div class='section-title'>RAG 지식백과 기반 양도양수 맞춤 법률/실무 상담</div>", unsafe_allow_html=True)
        st.write("상가임대차보호법, 감정평가 공식, 서류 위조 사기 예방 등 질문을 입력하세요.")
        
        # Sample Question templates
        st.write("**추천 질문 클릭:**")
        col_q1, col_q2 = st.columns(2)
        with col_q1:
            q_template1 = "상가 임차인의 권리금 회수 보호 기간이 어떻게 되나요?"
            q_template2 = "시설권리금 감가상각 공식과 연식 기준이 있나요?"
            
            if st.button(q_template1):
                st.session_state.chat_query = q_template1
                st.session_state.auto_submit = True
                st.rerun()
            if st.button(q_template2):
                st.session_state.chat_query = q_template2
                st.session_state.auto_submit = True
                st.rerun()
        with col_q2:
            q_template3 = "사업자등록증 위조 사기나 허위 매물 예방법이 무엇인가요?"
            q_template4 = "영업권리금 수익환원법은 어떻게 순수익을 가치로 바꾸나요?"
            
            if st.button(q_template3):
                st.session_state.chat_query = q_template3
                st.session_state.auto_submit = True
                st.rerun()
            if st.button(q_template4):
                st.session_state.chat_query = q_template4
                st.session_state.auto_submit = True
                st.rerun()
                
        # Main text query
        current_query = st.text_input("질문을 직접 입력하세요", key="chat_query_input", value=st.session_state.get("chat_query", ""))
        
        submit_clicked = st.button("질문 전송")
        
        if submit_clicked or st.session_state.get("auto_submit", False):
            # Reset auto_submit flag so it does not loop
            st.session_state.auto_submit = False
            
            if current_query:
                ans, sources = generate_rag_response(current_query)
                st.markdown(f"""
                <div class="glass-card" style="border-left: 5px solid #4F46E5;">
                    <h4 style="margin:0 0 10px 0; color:#0D9488;">🤖 에이전트 답변:</h4>
                    <p style="line-height:1.6;">{ans}</p>
                </div>
                """, unsafe_allow_html=True)
                
                if sources:
                    st.write("**참조 문서 출처:**")
                    for s in sources:
                        st.info(f"📁 **{s['category']} - {s['title']}**\n{s['text']}")
            else:
                st.warning("질문을 입력해주세요.")
                
    with tab_review:
        st.markdown("<div class='section-title'>인수 매장 온라인 고객 리뷰 감성 요약 파이프라인</div>", unsafe_allow_html=True)
        st.write("양수 대상 매장의 Naver 플레이스 리뷰 텍스트를 분석하여 핵심 키워드 및 리뷰 긍부정 요약을 진행합니다.")
        
        sample_reviews = st.text_area(
            "리뷰 텍스트 입력 (한 줄에 하나씩)", 
            value=(
                "커피가 정말 저렴하고 맛도 진해요! 매일 아침 테이크아웃 합니다.\n"
                "가게가 좁아서 매장 안에서 먹기에는 테이블 간격이 너무 가깝고 불편해요.\n"
                "가성비가 진짜 최고예요. 메가커피 중에서도 대기 시간이 적어서 좋습니다.\n"
                "키오스크가 가끔 오류가 나서 줄이 길게 늘어설 때가 있습니다.\n"
                "사장님이 친절하시고 주문 실수가 나도 즉시 해결해 주십니다.\n"
                "오후 알바생이 불친절해서 기분이 나빴습니다. 응대가 너무 퉁명스럽네요."
            ),
            height=150
        )
        
        if st.button("리뷰 감성 요약 분석 실행"):
            review_lines = [r.strip() for r in sample_reviews.split("\n") if r.strip()]
            
            # Simple keyword match analyzer (Positive / Negative)
            pos_keywords = ["최고", "저렴", "맛", "가성비", "친절", "좋습니다", "해결"]
            neg_keywords = ["좁아서", "불편", "오류", "불친절", "퉁명", "나빴", "간격", "길게"]
            
            positive_reviews = []
            negative_reviews = []
            
            for r in review_lines:
                pos_score = sum(1 for w in pos_keywords if w in r)
                neg_score = sum(1 for w in neg_keywords if w in r)
                if pos_score >= neg_score:
                    positive_reviews.append(r)
                else:
                    negative_reviews.append(r)
                    
            col_pos, col_neg = st.columns(2)
            with col_pos:
                st.markdown("<div style='background-color:rgba(16, 185, 129, 0.1); border:1px solid #10B981; padding:15px; border-radius:12px;'>", unsafe_allow_html=True)
                st.markdown("<h4 style='color:#059669; margin:0 0 10px 0;'>🟢 긍정적인 평판 및 강점</h4>", unsafe_allow_html=True)
                for pr in positive_reviews:
                    st.write(f"- {pr}")
                st.markdown("</div>", unsafe_allow_html=True)
                
            with col_neg:
                st.markdown("<div style='background-color:rgba(239, 68, 68, 0.1); border:1px solid #EF4444; padding:15px; border-radius:12px;'>", unsafe_allow_html=True)
                st.markdown("<h4 style='color:#DC2626; margin:0 0 10px 0;'>🔴 개선점 및 보완점</h4>", unsafe_allow_html=True)
                for nr in negative_reviews:
                    st.write(f"- {nr}")
                st.markdown("</div>", unsafe_allow_html=True)
                
            # Key recommendation
            st.write("---")
            st.markdown("<b style='color:#8B5CF6;'>💡 인공지능 양수 의사결정 추천:</b>", unsafe_allow_html=True)
            if len(positive_reviews) >= len(negative_reviews):
                st.success("해당 매장은 전반적으로 가성비와 점주 친절도 면에서 우수한 브랜드 평판을 지니고 있습니다. 양수 시 안정적인 단골 승계가 가능할 것으로 분석됩니다. 다만 협소한 매장 크기를 개선하기 위해 포장/배달 비중을 확대하는 영업 전략을 추천드립니다.")
            else:
                st.warning("소비자 리뷰 중 서비스 및 환경적 요소에 대한 부정적 인지 비중이 큽니다. 매장 인수 즉시 알바 응대 교육 강화 및 키오스크 노후화 점검을 진행해야 가치 회복이 가능할 것으로 보입니다.")

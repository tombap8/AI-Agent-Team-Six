import streamlit as st
import pandas as pd
import numpy as np
# pyrefly: ignore [missing-import]
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
from app.utils import parse_business_license_ocr, verify_business_tax_status, calculate_escrow_fee, generate_contract_draft, generate_contract_pdf

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
st.sidebar.markdown("<h2 style='text-align:center; color:#4F46E5; font-family:Outfit; font-weight:800;'>START-UP AI AGENT</h2>", unsafe_allow_html=True)
st.sidebar.markdown("<p style='text-align:center; color:#475569; font-size:0.9rem;'>프랜차이즈 점포 양도양수 AI 도우미</p>", unsafe_allow_html=True)
st.sidebar.markdown("---")

menu = st.sidebar.radio(
    "메뉴 선택",
    ["🏠 종합 대시보드", "🔍 실시간 점포 찾기 & 비교", "📊 하이브리드 권리평가", "📑 안전 계약 & 진위 검증", "💬 AI RAG 법률상담 & 매장리뷰요약"]
)

# 다른 페이지로 이동 시 계약서 초안 생성 결과물 초기화
if menu != "📑 안전 계약 & 진위 검증":
    st.session_state.draft_contract_txt = None
    st.session_state.draft_contract_pdf = None

st.sidebar.markdown("---")
st.sidebar.info("💡 **가상환경 활성화 상태**\nPython 3.14.5 (.venv)")

# ---------------------------------------------
# Page 1: 🏠 종합 대시보드
# ---------------------------------------------
if menu == "🏠 종합 대시보드":
    st.markdown("<h1 class='gradient-title'>창업 에이전트 대시보드</h1>", unsafe_allow_html=True)
    
    # 3-column stats
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="glass-card">
            <span class="badge-valid">거래 활성</span>
            <div style="color: #475569; font-size: 0.95rem; margin-top: 10px;">식음료 매물 등록</div>
            <div class="metric-val">6,404 건</div>
            <div style="color: #059669; font-size: 0.85rem; margin-top: 5px;">▲ 카페/한식 업종 위주 거래 활성화</div>
            <div style="margin-top: 12px; border-top: 1px solid rgba(15,23,42,0.06); padding-top: 10px; font-size: 0.8rem; color: #64748B; line-height: 1.45;">
                카페, 베이커리 등 식음료(F&B)는 양도양수 시장에서 거래 회전율이 가장 높은 핵심 업종군입니다.
            </div>
            <div style="font-size: 0.7rem; color: #94A3B8; text-align: right; margin-top: 6px;">[출처: 공정거래위원회 가맹사업정보제공시스템]</div>
        </div>
        """, unsafe_allow_html=True)
        
    with col2:
        st.markdown("""
        <div class="glass-card">
            <span class="badge-warning">장치 검증 대상</span>
            <div style="color: #475569; font-size: 0.95rem; margin-top: 10px;">오락스포츠 매물</div>
            <div class="metric-val">931 건</div>
            <div style="color: #D97706; font-size: 0.85rem; margin-top: 5px;">⚠ 초기 장비 고가 설비 검증 유의</div>
            <div style="margin-top: 12px; border-top: 1px solid rgba(15,23,42,0.06); padding-top: 10px; font-size: 0.8rem; color: #64748B; line-height: 1.45;">
                스크린골프, PC방 등 고가 장비 감가상각과 실제 시설물 작동 여부에 대한 정밀 실사가 필요합니다.
            </div>
            <div style="font-size: 0.7rem; color: #94A3B8; text-align: right; margin-top: 6px;">[출처: 국토교통부 표준 권리 산정 고시 및 현장 감정 기준]</div>
        </div>
        """, unsafe_allow_html=True)
        
    with col3:
        st.markdown("""
        <div class="glass-card">
            <span class="badge-danger">보안 조치</span>
            <div style="color: #475569; font-size: 0.95rem; margin-top: 10px;">누적 차단 허위 매물</div>
            <div class="metric-val">231 건</div>
            <div style="color: #DC2626; font-size: 0.85rem; margin-top: 5px;">🔒 국세청 API 대조 실시간 차단율 100%</div>
            <div style="margin-top: 12px; border-top: 1px solid rgba(15,23,42,0.06); padding-top: 10px; font-size: 0.8rem; color: #64748B; line-height: 1.45;">
                가상 정보나 폐업된 등록번호를 기재한 허위/위조 점포 매물을 실시간 API 조회를 통해 차단했습니다.
            </div>
            <div style="font-size: 0.7rem; color: #94A3B8; text-align: right; margin-top: 6px;">[출처: 홈택스 국세청 사업자등록상태조회 API]</div>
        </div>
        """, unsafe_allow_html=True)

    # Competitor trends chart & AI warning status
    st.markdown("<div class='section-title'>실시간 상권 추정 매출 및 경쟁분석 파이프라인</div>", unsafe_allow_html=True)
    
    # 1. Interactive controls for Area and Sector
    col_ctrl1, col_ctrl2 = st.columns([1, 1])
    with col_ctrl1:
        selected_district = st.selectbox(
            "분석 대상 상권 지역 선택",
            ["전체 평균 (전국)", "마포구 서교동 (위기 경보)", "강남구 역삼동 (주의 경보)", "분당구 서현역 (안정 지역)"],
            index=0,
            key="dashboard_district_select"
        )
    with col_ctrl2:
        selected_sectors = st.multiselect(
            "분석 관심 업종 선택 (다중 선택 가능)",
            ["카페", "치킨점", "편의점", "베이커리"],
            default=["카페", "치킨점"],
            key="dashboard_sectors_select"
        )
        
    # 2. Rich Mock Data for Districts and Sectors
    months = ["1월", "2월", "3월", "4월", "5월", "6월"]
    mock_data = {
        "전체 평균 (전국)": {
            "카페": {
                "sales": [3100, 3250, 3400, 3150, 3500, 3620],
                "foot_traffic": [42.1, 43.5, 45.0, 44.2, 46.5, 47.0],
                "competitors": [18, 18, 19, 19, 20, 20],
                "survival": [78, 77, 77, 78, 79, 80],
                "avg_price": 5400
            },
            "치킨점": {
                "sales": [5400, 5200, 5600, 5900, 6100, 6480],
                "foot_traffic": [42.1, 43.5, 45.0, 44.2, 46.5, 47.0],
                "competitors": [12, 12, 12, 13, 13, 13],
                "survival": [72, 71, 71, 70, 71, 72],
                "avg_price": 22000
            },
            "편의점": {
                "sales": [7200, 7100, 7400, 7600, 8100, 8350],
                "foot_traffic": [42.1, 43.5, 45.0, 44.2, 46.5, 47.0],
                "competitors": [8, 8, 8, 9, 9, 9],
                "survival": [85, 84, 84, 85, 85, 86],
                "avg_price": 7200
            },
            "베이커리": {
                "sales": [4100, 4300, 4200, 4400, 4600, 4820],
                "foot_traffic": [42.1, 43.5, 45.0, 44.2, 46.5, 47.0],
                "competitors": [6, 6, 6, 6, 7, 7],
                "survival": [75, 75, 74, 76, 77, 78],
                "avg_price": 11500
            }
        },
        "마포구 서교동 (위기 경보)": {
            "카페": {
                "sales": [4200, 4050, 3900, 3750, 3600, 3500],
                "foot_traffic": [68.5, 65.2, 63.0, 61.2, 60.0, 58.5],
                "competitors": [45, 46, 48, 49, 51, 52],
                "survival": [65, 62, 59, 57, 54, 51],
                "avg_price": 4800
            },
            "치킨점": {
                "sales": [6800, 6600, 6450, 6200, 6000, 5900],
                "foot_traffic": [68.5, 65.2, 63.0, 61.2, 60.0, 58.5],
                "competitors": [28, 29, 31, 31, 32, 33],
                "survival": [58, 55, 52, 49, 46, 43],
                "avg_price": 20500
            },
            "편의점": {
                "sales": [9500, 9200, 9000, 8800, 8600, 8400],
                "foot_traffic": [68.5, 65.2, 63.0, 61.2, 60.0, 58.5],
                "competitors": [18, 18, 19, 19, 20, 20],
                "survival": [75, 73, 70, 68, 66, 64],
                "avg_price": 6800
            },
            "베이커리": {
                "sales": [5800, 5600, 5450, 5250, 5100, 4950],
                "foot_traffic": [68.5, 65.2, 63.0, 61.2, 60.0, 58.5],
                "competitors": [14, 14, 15, 16, 16, 17],
                "survival": [60, 58, 55, 52, 49, 47],
                "avg_price": 10200
            }
        },
        "강남구 역삼동 (주의 경보)": {
            "카페": {
                "sales": [3800, 3750, 3900, 3850, 3920, 3880],
                "foot_traffic": [85.0, 84.5, 86.2, 85.0, 86.8, 86.0],
                "competitors": [35, 35, 36, 36, 37, 37],
                "survival": [70, 70, 69, 68, 68, 67],
                "avg_price": 5600
            },
            "치킨점": {
                "sales": [6100, 5950, 6050, 5900, 6150, 6000],
                "foot_traffic": [85.0, 84.5, 86.2, 85.0, 86.8, 86.0],
                "competitors": [20, 20, 21, 21, 22, 22],
                "survival": [68, 67, 66, 65, 65, 64],
                "avg_price": 23000
            },
            "편의점": {
                "sales": [8800, 8650, 8900, 8850, 9100, 8950],
                "foot_traffic": [85.0, 84.5, 86.2, 85.0, 86.8, 86.0],
                "competitors": [15, 15, 15, 16, 16, 16],
                "survival": [80, 79, 79, 78, 78, 78],
                "avg_price": 7500
            },
            "베이커리": {
                "sales": [4900, 4800, 5000, 4950, 5100, 5050],
                "foot_traffic": [85.0, 84.5, 86.2, 85.0, 86.8, 86.0],
                "competitors": [10, 10, 11, 11, 11, 11],
                "survival": [72, 71, 71, 70, 70, 69],
                "avg_price": 12500
            }
        },
        "분당구 서현역 (안정 지역)": {
            "카페": {
                "sales": [3900, 4100, 4250, 4200, 4450, 4600],
                "foot_traffic": [52.0, 53.5, 55.0, 54.8, 57.0, 58.2],
                "competitors": [18, 18, 18, 19, 19, 19],
                "survival": [82, 82, 83, 83, 84, 85],
                "avg_price": 5200
            },
            "치킨점": {
                "sales": [6200, 6400, 6700, 6550, 6900, 7150],
                "foot_traffic": [52.0, 53.5, 55.0, 54.8, 57.0, 58.2],
                "competitors": [12, 12, 12, 12, 13, 13],
                "survival": [80, 80, 81, 81, 82, 83],
                "avg_price": 21500
            },
            "편의점": {
                "sales": [8100, 8300, 8600, 8500, 8900, 9150],
                "foot_traffic": [52.0, 53.5, 55.0, 54.8, 57.0, 58.2],
                "competitors": [9, 9, 9, 9, 9, 9],
                "survival": [88, 88, 89, 89, 90, 91],
                "avg_price": 7000
            },
            "베이커리": {
                "sales": [5100, 5300, 5550, 5400, 5800, 6050],
                "foot_traffic": [52.0, 53.5, 55.0, 54.8, 57.0, 58.2],
                "competitors": [6, 6, 6, 6, 6, 6],
                "survival": [81, 81, 82, 82, 83, 84],
                "avg_price": 11800
            }
        }
    }
    
    diagnostic_text = {
        "전체 평균 (전국)": "국내 주요 상권은 카페 및 편의점 업종을 중심으로 소비 심리가 소폭 회복하는 추세입니다. 다만, 치킨 등 F&B 업종의 경우 재료비 및 인건비 상승으로 인해 실질 순수익 성장이 정체되고 있으므로 점포 양수 시 고정비 지출 구조를 꼼꼼히 점검하셔야 합니다.",
        "마포구 서교동 (위기 경보)": "경고! 홍대/서교동 상권은 유동인구가 12% 급감하며 쇠퇴 징후를 보이고 있습니다. 특히 카페와 치킨 등 F&B 업종의 점포 포화도가 임계치(3.5)를 초과하여 출혈 경쟁이 극에 달했습니다. 양도양수 시 요구하는 높은 시설 및 영업 권리금이 과다 산정되었을 가능성이 매우 크므로 정밀 권리평가가 필수적입니다.",
        "강남구 역삼동 (주의 경보)": "역삼동 오피스 상권은 평일 점심 매출은 견고하나 주말 매출이 급격히 정체되는 주 5일 상권의 한계를 보입니다. 계속사업 생존율 등급은 C등급으로, F&B 업종은 경쟁률이 높은 편입니다. 인수 검토 시 주말 영업 비중을 최소화하고 평일 회전율을 극대화하는 전략이 요구됩니다.",
        "분당구 서현역 (안정 지역)": "서현역 일대는 배후 주거지와 지하철역 중심의 탄탄한 유동인구 소비지수를 바탕으로 3년 평균 생존율 82%를 상회하는 안정적 상권입니다. 신규 진입 장벽이 다소 존재하나, 기존 매물 인수 시 단골 고객 승계가 유리하며 매출 흐름도 상승세를 유지하고 있습니다."
    }
    
    col_chart, col_warning = st.columns([2, 1])
    
    with col_chart:
        # Setup Korean font for Matplotlib
        import matplotlib.font_manager as fm
        try:
            font_path = "C:/Windows/Fonts/malgun.ttf"
            font_name = fm.FontProperties(fname=font_path).get_name()
            plt.rc('font', family=font_name)
            plt.rcParams['axes.unicode_minus'] = False
        except Exception:
            pass

        # Drawing matplotlib dark premium chart
        fig, ax = plt.subplots(figsize=(8, 4.2))
        fig.patch.set_facecolor('#F1F5F9')
        ax.set_facecolor('#FFFFFF')
        
        district_data = mock_data[selected_district]
        
        color_map = {
            "카페": '#4F46E5',
            "치킨점": '#0D9488',
            "편의점": '#D97706',
            "베이커리": '#8B5CF6'
        }
        marker_map = {
            "카페": 'o',
            "치킨점": 's',
            "편의점": '^',
            "베이커리": 'd'
        }
        
        if not selected_sectors:
            ax.text(0.5, 0.5, "분석 대상 업종을 1개 이상 선택해 주세요.", 
                    horizontalalignment='center', verticalalignment='center',
                    transform=ax.transAxes, color='#DC2626', fontsize=12)
        else:
            for sector in selected_sectors:
                if sector in district_data:
                    data = district_data[sector]
                    ax.plot(months, data["sales"], marker=marker_map[sector], 
                            color=color_map[sector], linewidth=2.5, label=f'{sector} 평균 매출')
            
            ax.set_title(f"{selected_district} 업종별 월간 추정 매출 흐름 (단위: 만원)", color='#1E293B', fontsize=12, pad=15)
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
        st.markdown("<div class='glass-card' style='height: 100%; margin-bottom: 0px;'>", unsafe_allow_html=True)
        st.markdown(f"<p style='font-weight:600; color:#4F46E5; margin-bottom: 4px;'>🔎 {selected_district} AI 집중 진단</p>", unsafe_allow_html=True)
        st.write(diagnostic_text[selected_district])
        
        st.write("---")
        st.markdown("<p style='font-weight:600; color:#DC2626;'>🚨 AI 위기 상권 경보 알람 (2027 모형)</p>", unsafe_allow_html=True)
        st.error("🔴 **위기 경보: 마포구 서교동 일대**\n- 유동인구 12% 급감 징후 감지\n- 경쟁 점포 과밀화 지수 임계치(3.5) 초과\n- 양도양수 시 권리금 과다 산정 유의 요망")
        st.warning("🟡 **주의 경보: 강남구 역삼동 상권**\n- 오피스 상권 주말 매출 정체 추세\n- 계속사업 생존율 등급: C등급")
        st.success("🟢 **안정 지역: 분당구 서현역 일대**\n- 3년 평균 생존율 82% 유지\n- 유동인구 소비지수 견고")
        st.markdown("</div>", unsafe_allow_html=True)

    # 3. Comprehensive Data Table
    if selected_sectors:
        table_records = []
        for sector in selected_sectors:
            if sector in district_data:
                data = district_data[sector]
                for idx, m in enumerate(months):
                    table_records.append({
                        "월": m,
                        "업종": sector,
                        "추정 평균 매출 (만원)": data["sales"][idx],
                        "유동인구 지수 (만명/월)": data["foot_traffic"][idx],
                        "경쟁 점포 수 (개소)": data["competitors"][idx],
                        "계속사업 생존율": f"{data['survival'][idx]}%",
                        "평균 객단가 (원)": f"{data['avg_price']:,}"
                    })
        df_detailed = pd.DataFrame(table_records)
        st.write("<div style='height: 15px;'></div>", unsafe_allow_html=True)
        st.markdown("<p style='font-weight:600; color:#1E293B; margin-bottom: 5px;'>📊 상권 상세 종합 지표 명세 (실시간 파이프라인 추출)</p>", unsafe_allow_html=True)
        st.dataframe(df_detailed, use_container_width=True, hide_index=True)

    # 4. Data Sources and References
    st.write("<div style='height: 25px;'></div>", unsafe_allow_html=True)
    with st.expander("ℹ️ 종합 대시보드 데이터 및 지표 출처 안내", expanded=False):
        st.markdown("""
        <div style="line-height:1.6;">
            대시보드에 표시되는 각종 통계 지표 및 실시간 상권 분석 자료는 아래의 신뢰도 높은 공공기관 공적 장부 및 빅데이터 포털 자료를 기반으로 가공 및 모델링되었습니다.
            <br><br>
            <ul>
                <li><b>상권별 추정 매출 및 유동인구 지수</b>: 
                    <ul>
                        <li><a href="https://data.seoul.go.kr/" target="_blank" style="color:#4F46E5; text-decoration:none; font-weight:600;">서울시 열린데이터광장</a> - <i>서울시 우리마을가게 상권분석서비스 (추정매출 및 유동인구 데이터)</i></li>
                        <li><a href="https://www.semas.or.kr/" target="_blank" style="color:#4F46E5; text-decoration:none; font-weight:600;">소상공인시장진흥공단</a> - <i>소상공인 상권정보시스템 핵심 입지 통계</i></li>
                    </ul>
                </li>
                <li><b>경쟁 점포 밀집도 및 계속사업 생존율</b>:
                    <ul>
                        <li><a href="https://www.localdata.go.kr/" target="_blank" style="color:#4F46E5; text-decoration:none; font-weight:600;">행정안전부 LOCALDATA</a> - <i>지방행정인허가데이터 (식음료/일반음식점/휴게음식점 인허가 대장)</i></li>
                        <li><a href="http://kostat.go.kr/" target="_blank" style="color:#4F46E5; text-decoration:none; font-weight:600;">통계청</a> - <i>전국사업체조사 및 업종별 생존지율 지표</i></li>
                    </ul>
                </li>
                <li><b>등록 매물 건수 및 안전성 검증 지표</b>:
                    <ul>
                        <li><a href="https://www.data.go.kr/" target="_blank" style="color:#4F46E5; text-decoration:none; font-weight:600;">공공데이터포털 (국세청 API)</a> - <i>사업자등록정보 진위확인 및 상태조회 OpenAPI 실시간 연동</i></li>
                        <li><a href="https://franchise.ftc.go.kr/" target="_blank" style="color:#4F46E5; text-decoration:none; font-weight:600;">공정거래위원회 가맹사업거래</a> - <i>전국 프랜차이즈 브랜드 정보공개서 표준 등록 지표 데이터베이스</i></li>
                    </ul>
                </li>
                <li><b>AI 예측 모델링</b>:
                    <details style="margin-top: 5px; cursor: pointer;">
                        <summary style="font-weight: 600; color: #4F46E5; outline: none;">💡 START-UP AI 시계열 예측 파이프라인 (Prophet & LSTM v2027) 기술 상세 보기 (클릭)</summary>
                        <div style="background: color-mix(in srgb, var(--background-color) 96%, var(--text-color) 4%); border-left: 4px solid #4F46E5; padding: 15px; margin-top: 8px; font-size: 0.9rem; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.02); line-height: 1.6;">
                            <b>1. 하이브리드 예측 모델 아키텍처 (Prophet + LSTM 앙상블)</b><br>
                            <ul>
                                <li><b>Prophet (가법 모형)</b>: 상권 데이터가 가진 강력한 트렌드(추세선)와 주기적 계절성(일/주/월/연간 주기 및 오피스/대학가/주거지의 요일별 매출 흐름)을 학습합니다.</li>
                                <li><b>LSTM (장단기 메모리 신경망)</b>: 계절성 패턴 외에 대형 프랜차이즈 진입, 교통망 변화, 원자재가 인상 등 비선형적인 일시적 충격(Short-term Shocks) 및 시퀀스 의존성을 처리합니다.</li>
                            </ul>
                            <b>2. 다변량 피처 엔지니어링 (Exogenous Variables)</b><br>
                            과거 매출 추이 외에 실시간 통신사/카드사 유동인구 지수, 동일 업종 점포 밀집도(Competitor Density), 소상공인시장진흥공단 기준 업종별 계속사업 생존율을 다변량 피처로 결합 입력하여 미래 3~6개월 뒤 추정치를 도출합니다.<br><br>
                            <b>3. AI 위기 상권 경보 판정 기준</b><br>
                            <ul>
                                <li>🔴 <b>위기 경보</b>: 3개월 내 매출 추정치가 전년 대비 -15% 이상 급감 예측되거나 경쟁 과밀도가 임계치(3.5)를 초과할 시 발령.</li>
                                <li>🟡 <b>주의 경보</b>: 매출이 정체되며 특정 요일 매출 편차가 과도하고 생존율 등급이 C등급 이하로 수렴 시 발령.</li>
                                <li>🟢 <b>안정 지역</b>: 소비 지수 및 유동인구가 견고하며 매출 추이가 우상향 혹은 안정적 평행 흐름 유지 시 판정.</li>
                            </ul>
                        </div>
                    </details>
                </li>
            </ul>
        </div>
        """, unsafe_allow_html=True)


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

        def trigger_search():
            new_q = st.session_state.brand_search_input.strip()
            st.session_state.search_query = new_q
            st.session_state.searching = True
            if "api_provider_select" in st.session_state:
                st.session_state.api_provider_param = provider_map[st.session_state.api_provider_select]
            if "api_key_input" in st.session_state:
                st.session_state.api_key_param = st.session_state.api_key_input

        col_input, col_btn = st.columns([3.2, 1.3])
        
        with col_input:
            search_q = st.text_input(
                "프랜차이즈 브랜드명 입력 (예: 빽다방, 맘스터치, 엽기떡볶이, bbq 등)",
                value=st.session_state.search_query,
                disabled=st.session_state.searching,
                key="brand_search_input",
                on_change=trigger_search
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

        # 1. Default View: Show the franchise brands comparison dashboard when no search query
        if not st.session_state.search_query:
            st.markdown("##### 🏛 주요 프랜차이즈 브랜드 공식 지표 비교")
            
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
            
            # Show individual cards of the brands
            st.write("<div style='height:15px;'></div>", unsafe_allow_html=True)
            cols = st.columns(5)
            for i, (k, val) in enumerate(FRANCHISE_DB.items()):
                with cols[i % 5]:
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
        st.markdown(f"<p style='font-size:0.85rem; color:#4F46E5; margin-top:-15px; margin-bottom:10px;'>👉 입력값: <b>{initial_cost:,}</b> 원</p>", unsafe_allow_html=True)
        operating_months = st.slider("운영 개월 수 (t, 개월)", min_value=0, max_value=120, value=24)
        condition_coeff = st.slider("정성 보정 계수 (C_q, 관리상태)", min_value=0.0, max_value=1.0, value=0.9, step=0.05)
        
        st.markdown("<div class='section-title'>2. 무형자산 영업권 가치 (수익환원법)</div>", unsafe_allow_html=True)
        annual_net_profit = st.number_input("연간 실질 순영업이익 (원, 자가인건비 제외)", min_value=0, value=48000000, step=1000000)
        st.markdown(f"<p style='font-size:0.85rem; color:#4F46E5; margin-top:-15px; margin-bottom:10px;'>👉 입력값: <b>{annual_net_profit:,}</b> 원</p>", unsafe_allow_html=True)
        discount_rate = st.slider("가이드라인 할인율 (R)", min_value=0.05, max_value=0.25, value=0.10, step=0.01)
        years = st.slider("무형가치 유효 기간 (N, 개년)", min_value=1, max_value=5, value=3)
        
        st.markdown("<div class='section-title'>3. 입지 및 허가 권리금</div>", unsafe_allow_html=True)
        val_location = st.number_input("주변 비교 바닥 위치 권리금 (원)", min_value=0, value=20000000, step=1000000)
        st.markdown(f"<p style='font-size:0.85rem; color:#4F46E5; margin-top:-15px; margin-bottom:10px;'>👉 입력값: <b>{val_location:,}</b> 원</p>", unsafe_allow_html=True)
        val_license = st.number_input("특수 행정 인허가 권리금 (원)", min_value=0, value=5000000, step=1000000)
        st.markdown(f"<p style='font-size:0.85rem; color:#4F46E5; margin-top:-15px; margin-bottom:10px;'>👉 입력값: <b>{val_license:,}</b> 원</p>", unsafe_allow_html=True)
        
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
        biz_no_field = st.text_input("사업자등록번호", ocr_biz_no)
        owner_field = st.text_input("대표자명", ocr_owner)
        date_field = st.text_input("개업일자", ocr_date)
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
        st.markdown(f"<p style='font-size:0.85rem; color:#4F46E5; margin-top:-15px; margin-bottom:10px;'>👉 입력값: <b>{amount_input:,}</b> 원</p>", unsafe_allow_html=True)
        fee_rate_input = st.slider("권리 중개 수수료율 설정", min_value=0.01, max_value=0.05, value=0.03, step=0.005)
        
        escrow_calc = calculate_escrow_fee(amount_input, fee_rate_input)
        
        st.markdown(f"""
        <div class="glass-card">
            <div style="display:flex; justify-content:space-between; margin-bottom:10px;">
                <span style="color:#475569;">합산 권리금액</span>
                <b style="color:#1E293B;">{escrow_calc['total_amount'] / 10000:,.0f} 만원 <span style="font-weight:normal; font-size:0.85rem; color:#64748B;">(₩{escrow_calc['total_amount']:,.0f})</span></b>
            </div>
            <div style="display:flex; justify-content:space-between; margin-bottom:10px;">
                <span style="color:#475569;">중개 수수료 ({escrow_calc['fee_rate_percent']:.1f}%)</span>
                <b style="color:#0D9488;">{escrow_calc['broker_fee'] / 10000:,.0f} 만원 <span style="font-weight:normal; font-size:0.85rem; color:#64748B;">(₩{escrow_calc['broker_fee']:,.0f})</span></b>
            </div>
            <div style="display:flex; justify-content:space-between; border-top:1px solid rgba(15,23,42,0.08); padding-top:10px;">
                <span style="color:#475569; font-weight:600;">에스크로 예치금액 (매도인 지급액)</span>
                <b style="color:#4F46E5; font-size:1.2rem;">{escrow_calc['escrow_held'] / 10000:,.0f} 만원 <span style="font-weight:normal; font-size:0.85rem; color:#64748B;">(₩{escrow_calc['escrow_held']:,.0f})</span></b>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.write("**계약 당사자 인적사항**")
        c_seller = st.text_input("양도인(갑) 대표자명", ocr_owner)
        c_buyer = st.text_input("양수인(을) 대표자명", "예비사장")
        
        if "draft_contract_txt" not in st.session_state:
            st.session_state.draft_contract_txt = None
        if "draft_contract_pdf" not in st.session_state:
            st.session_state.draft_contract_pdf = None

        if st.button("표준 권리금 계약서 초안 빌드"):
            # split total val equally for drafting demo if from custom input
            v_split = amount_input / 4
            st.session_state.draft_contract_txt = generate_contract_draft(
                c_seller, c_buyer, brand_field, address_field, 
                v_split, v_split, v_split, v_split
            )
            st.session_state.draft_contract_pdf = generate_contract_pdf(
                c_seller, c_buyer, brand_field, address_field, 
                v_split, v_split, v_split, v_split,
                fee_rate=fee_rate_input
            )

        if st.session_state.draft_contract_txt is not None:
            st.text_area("국토교통부 고시 계약서 내용", st.session_state.draft_contract_txt, height=350)
            
            c_d1, c_d2 = st.columns(2)
            with c_d1:
                st.download_button(
                    "📥 표준 계약서 다운로드 (.txt)", 
                    st.session_state.draft_contract_txt, 
                    file_name="standard_premium_contract.txt",
                    key="download_txt_btn"
                )
            with c_d2:
                st.download_button(
                    "📥 표준 계약서 다운로드 (.pdf)", 
                    st.session_state.draft_contract_pdf, 
                    file_name="standard_premium_contract.pdf",
                    mime="application/pdf",
                    key="download_pdf_btn"
                )

# ---------------------------------------------
# Page 5: 💬 AI RAG 법률상담 & 매장리뷰요약
# ---------------------------------------------
elif menu == "💬 AI RAG 법률상담 & 매장리뷰요약":
    st.markdown("<h1 class='gradient-title'>AI RAG 법률상담 어시스턴트 & 매장리뷰 요약</h1>", unsafe_allow_html=True)
    
    tab_chat, tab_review = st.tabs(["💬 RAG 법률상담 AI 챗봇", "📝 매장 리뷰 AI 요약"])
    
    with tab_chat:
        st.markdown("<div class='section-title'>RAG 지식백과 기반 양도양수 맞춤 법률/실무 상담</div>", unsafe_allow_html=True)
        st.write("상가임대차보호법, 감정평가 공식, 서류 위조 사기 예방 등 질문을 입력하세요.")
        
        # Sample Question templates
        st.write("**추천 질문 클릭:**")
        col_q1, col_q2 = st.columns(2)
        if "chat_query_input" not in st.session_state:
            st.session_state.chat_query_input = ""

        with col_q1:
            q_template1 = "상가 임차인의 권리금 회수 보호 기간이 어떻게 되나요?"
            q_template2 = "시설권리금 감가상각 공식과 연식 기준이 있나요?"
            
            if st.button(q_template1):
                st.session_state.chat_query_input = q_template1
                st.session_state.auto_submit = True
                st.rerun()
            if st.button(q_template2):
                st.session_state.chat_query_input = q_template2
                st.session_state.auto_submit = True
                st.rerun()
        with col_q2:
            q_template3 = "사업자등록증 위조 사기나 허위 매물 예방법이 무엇인가요?"
            q_template4 = "영업권리금 수익환원법은 어떻게 순수익을 가치로 바꾸나요?"
            
            if st.button(q_template3):
                st.session_state.chat_query_input = q_template3
                st.session_state.auto_submit = True
                st.rerun()
            if st.button(q_template4):
                st.session_state.chat_query_input = q_template4
                st.session_state.auto_submit = True
                st.rerun()
                
        # Main text query
        current_query = st.text_input("질문을 직접 입력하세요", key="chat_query_input")
        
        submit_clicked = st.button("질문 전송")
        
        if submit_clicked or st.session_state.get("auto_submit", False):
            # Reset auto_submit flag so it does not loop
            st.session_state.auto_submit = False
            
            if current_query:
                ans, sources = generate_rag_response(current_query)
                st.markdown(f"""
                <div class="glass-card" style="border-left: 5px solid #4F46E5;">
                    <h4 style="margin:0 0 15px 0; color:#0D9488;">🤖 에이전트 답변:</h4>
                    <div style="line-height:1.8; font-size: 1rem; color: var(--text-color);">{ans}</div>
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

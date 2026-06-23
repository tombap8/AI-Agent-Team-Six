# 디자이너 Agent (style.md)

이 파일은 **퀀트투자 포트폴리오 웹 애플리케이션**의 디자인 톤앤매너와 UI/UX 요소의 스타일 가이드를 기재하는 문서입니다. 전체적으로 **"밝고 상큼한 시트러스 & 민트(Citrus & Mint)"** 느낌을 전달할 수 있도록 구성합니다.

---

## 🎨 디자인 컨셉 및 톤앤매너
- **메인 컨셉**: 밝고 상큼하여 유저에게 긍정적이고 신뢰감을 주는 금융 대시보드.
- **키워드**: Refreshing, Clean, Energetic, Trustworthy.

---

## 🎨 컬러 시스템 (Color Palette)

Streamlit의 밝은 테마에 어우러지는 활기찬 시트러스 계열의 색 조합을 사용합니다.

| 역할 | 색상 이름 | HEX 코드 | RGB / HSL | 느낌 및 사용 용도 |
| :--- | :--- | :--- | :--- | :--- |
| **Primary Accent** | Fresh Mint | `#00C49F` | `hsl(169, 100%, 38%)` | 포인트 컬러, 선택된 버튼, 긍정적인 지표 |
| **Secondary Accent**| Lemon Yellow | `#FFD700` | `hsl(51, 100%, 50%)` | 하이라이트, 보조 포인트, 경고/주의 피드백 |
| **Brand Color** | Lime Green | `#85E313` | `hsl(87, 85%, 48%)` | 로고, 타이틀 포인트, 상큼한 메인 브랜드 톤 |
| **Background** | Clean Crisp | `#F7F9FA` | `hsl(210, 20%, 98%)` | 전체 웹 앱 메인 배경색 (Soft Gray-Blue) |
| **Card Background** | Pure White | `#FFFFFF` | `hsl(0, 0%, 100%)` | 대시보드 카드, 데이터 표 배경 |
| **Text Dark** | Deep Charcoal | `#1E293B` | `hsl(215, 25%, 27%)` | 메인 본문 및 굵은 타이틀 텍스트 |
| **Text Light** | Slate Muted | `#64748B` | `hsl(215, 16%, 47%)` | 부제목, 캡션, 힌트용 텍스트 |

---

## ✍️ 타이포그래피 (Typography)
- **메인 폰트**: 'Inter', 'Outfit' 및 한국어 가독성을 위한 'Noto Sans KR' 사용.
- **글자 크기 및 굵기 구성**:
  - `h1`: 32px (Bold, 700) - 화면의 주요 성격을 나타내는 대문자
  - `h2`: 24px (Semi-Bold, 600) - 섹션 구분선
  - `h3`: 18px (Medium, 500) - 카드 헤더 또는 소제목
  - `body`: 14px~16px (Regular, 400) - 주 데이터 수치 및 표 텍스트

---

## 🧩 UI/UX 스타일 가이드라인 (Streamlit 적용 기준)

Streamlit의 기본 레이아웃을 극대화하기 위해 다음과 같은 커스텀 CSS 가이드라인을 정의합니다.

### 1. 카드형 레이아웃 (Card Layout)
- 데이터 메트릭이나 개별 종목 요약본은 흰색 배경의 카드 형태로 시각적 경계를 둡니다.
- **스타일 속성**:
  - `background-color: #FFFFFF`
  - `border-radius: 12px`
  - `padding: 20px`
  - `box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03)` (매우 부드러운 그림자 효과)

### 2. 컴포넌트 요소 스타일
- **사이드바 (Sidebar)**: 배경색은 약간의 연초록 뉘앙스가 섞인 미색 또는 순백색을 사용하여 밝고 화사하게 유지합니다.
- **버튼 (Buttons)**: 기본 호버 효과는 Lime Green 또는 Fresh Mint 색상의 투명도 조절로 활기찬 느낌을 구현합니다.
- **탭 (Tabs)**: 퀄리티/밸류/모멘텀 등 각 지표 탭 전환 시, 슬라이드 애니메이션이나 테두리 하이라이트에 Mint/Lime Accent를 반영합니다.

### 3. 데이터 시각화 (Charts & Graphs)
- Plotly 등의 인터랙티브 라이브러리 사용 시, 차트 컬러 스케일도 시트러스/민트 테마를 준수합니다.
  - 상승 그래프: Fresh Mint (`#00C49F`)
  - 하락 그래프: Warm Red-Orange (`#FF6B6B` - 지나치게 칙칙하지 않은 산뜻한 코랄 레드)
  - 영역/파이 차트 채우기: 민트, 라임, 레몬, 소프트 스카이블루 계열의 그라데이션 조합 활용.

### 4. 기술적 분석 및 백테스트 시각화 개선 가이드 (Ch 15, 16 기반)
- **캔들스틱 차트 (Candlestick Charts)**:
  - 상승 캔들: Fresh Mint (`#00C49F`) 실선 채우기.
  - 하락 캔들: Coral Red (`#FF6B6B`) 실선 채우기.
- **보조지표 오버레이 (Indicator Overlays)**:
  - 볼린저 밴드(Bollinger Bands) 영역은 매우 옅은 민트 톤 (`rgba(0, 196, 159, 0.05)`)으로 투명하게 채워 주가 캔들과의 시각적 혼선을 방지합니다.
  - 이동평균선(MA)은 명도가 다른 연두/노랑 계열의 얇은 선(1.5px)으로 오버레이합니다.
- **백테스트 차트 (Backtest Lines)**:
  - 포트폴리오 누적 수익률 곡선: 두꺼운 Lime Green (`#85E313`, 3px 실선)으로 강조.
  - 벤치마크 누적 수익률 곡선: 차분한 Slate Gray (`#94A3B8`, 1.5px 점선)로 보조 처리.
- **매매 신호 표시 (Trade Signal Markers)**:
  - 매수 진입 시점: 주가 차트 하단에 녹색 상향 삼각형 (`▲`, `#00C49F`) 마커 표시.
  - 매도 청산 시점: 주가 차트 상단에 적색 하향 삼각형 (`▼`, `#FF6B6B`) 마커 표시.


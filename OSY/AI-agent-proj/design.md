# Design Specifications (design.md)

본 문서는 **점포창업(양도양수) 도우미 에이전트**의 UI/UX 디자인 가이드라인입니다. 단순한 MVP 형태를 탈피하고 사용자에게 신뢰감과 시각적 몰입감을 주는 프리미엄 디자인 요소를 규정합니다.

---

## 1. 디자인 컨셉: Glassmorphism & Light Premium
*   **기본 테마**: Light Mode & Soft White Glassmorphism (밝고 투명한 유리 질감 효과)
*   **핵심 가치**: 신뢰성(Reliability), 전문성(Expertise), 직관성(Intuitive UI)
*   **비주얼 요소**: 레이어간 부드러운 그림자 효과, 화사한 그라데이션, 반응형 마이크로 인터랙션

---

## 2. 디자인 토큰 및 컬러 팔레트 (Color Palette)

| 구분 | 색상명 | HSL / Hex Code | 용도 |
| :--- | :--- | :--- | :--- |
| **Primary** | Off-White / Slate 50 | `#F8FAFC` | 메인 백그라운드 배경색 |
| **Secondary** | White Glass Card | `rgba(255, 255, 255, 0.7)` | 카드 및 패널 배경 (글래스모피즘 투명도 포함) |
| **Accent 1** | Indigo Violet | `#4F46E5` | 메인 액션 버튼, 활성 메뉴, 중요 포인트 테두리 |
| **Accent 2** | Soft Teal | `#0D9488` | RAG 챗봇 답변 말풍선 데코, 그래프 핵심선 |
| **Success** | Emerald Green | `#10B981` | 안전 검증 완료, 적정 가격 상태 표시 |
| **Warning** | Amber Orange | `#D97706` | 권리금 과다 산정 경고, 보통 위험도 상권 |
| **Danger** | Crimson Red | `#DC2626` | 허위 매물 차단 경고, 위기 상권 조기 경보 |
| **Text Primary**| Dark Slate | `#1E293B` | 기본 타이틀 및 메인 텍스트 (높은 명도 대비) |
| **Text Secondary**| Muted Slate | `#475569` | 서브 타이틀 및 보조 설명 텍스트 |

---

## 3. UI/UX 레이아웃 설계

1.  **Typography**: 
    *   글로벌 폰트는 Google Fonts의 **Outfit**과 **Inter**를 로드하여 세련되고 모던한 타이포그래피 구현.
2.  **Sidebar Navigation**:
    *   좌측 사이드바는 불필요한 장식을 배제하고 아이콘과 세련된 라벨로 페이지 선택 지원.
3.  **Metrics Board**:
    *   주요 지표(권리금 총액, 상권 생존 지수, 안전도 등)는 입체감 있는 카드 형태로 구현하고, 하단에 미세한 그라데이션 보더를 삽입.
4.  **Premium AI Chatbot Interface**:
    *   상담 말풍선에 그라데이션 배경을 적용하고, 로봇 아이콘과 둥글게 처리된 글래스 필터를 조화시켜 메신저와 같은 몰입감 선사.

---

## 4. Streamlit 적용 커스텀 CSS (CSS Snippets)

Streamlit의 기본 레이아웃을 덮어쓰기 위해 `main.py`에 주입할 공통 CSS 스타일 템플릿입니다.

```css
/* Google Fonts 로드 */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&family=Outfit:wght@400;600;800&display=swap');

/* 테마 전환 시 부드러운 색상 반전을 위한 전역 transition 설정 */
.stApp, .stApp * {
    transition: background-color 0.5s ease, color 0.5s ease, border-color 0.5s ease, box-shadow 0.5s ease;
}

/* 전체 테마 바디 설정 */
.stApp {
    background-color: #F8FAFC;
    color: #1E293B;
    font-family: 'Inter', sans-serif;
}

/* 글래스모피즘 카드 스타일 */
.glass-card {
    background: rgba(255, 255, 255, 0.7);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    border-radius: 16px;
    border: 1px solid rgba(15, 23, 42, 0.08);
    padding: 24px;
    margin-bottom: 20px;
    box-shadow: 0 8px 32px 0 rgba(15, 23, 42, 0.06);
}

/* 주요 타이틀 그라데이션 */
.gradient-title {
    font-family: 'Outfit', sans-serif;
    font-weight: 800;
    background: linear-gradient(135deg, #4F46E5 0%, #0D9488 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-size: 2.5rem;
    margin-bottom: 1rem;
}

/* 커스텀 버튼 스타일 */
div.stButton > button:first-child {
    background: linear-gradient(135deg, #4F46E5 0%, #0D9488 100%);
    color: #FFFFFF;
    border: none;
    border-radius: 8px;
    padding: 10px 24px;
    font-weight: 600;
    transition: all 0.3s ease;
    box-shadow: 0 4px 15px rgba(79, 70, 229, 0.25);
}

div.stButton > button:first-child:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(79, 70, 229, 0.35);
}
```

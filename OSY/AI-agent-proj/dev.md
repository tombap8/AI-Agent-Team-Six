# Technical Specifications (dev.md)

본 문서는 **점포창업(양도양수) 도우미 에이전트**의 백엔드 기술 명세 및 개발 가이드라인입니다.

---

## 1. 개발 환경 및 필수 라이브러리 (Dependencies)
*   **언어**: Python 3.14.5
*   **메인 프레임워크**: Streamlit
*   **데이터베이스**: SQLite3 (표준 라이브러리 내장)
*   **패키지 종속성 (`requirements.txt`)**:
    *   `streamlit`: UI 구동
    *   `pandas`, `numpy`: 데이터 처리 및 수식 계산
    *   `matplotlib`: 상권 정보 및 매출 데이터 시각화 차트 생성
    *   `sentence-transformers`: RAG용 벡터 임베딩 및 유사도 검색 (로컬 경량화 모델 사용)
    *   `pdfplumber`: 공정위 정보공개서 PDF 등 텍스트 스크래핑 지원

---

## 2. 파일 및 폴더 구조
```
c:/AI-agent-proj/
│
├── .venv/                         # 파이썬 가상 환경
├── docs/                          # 요구사항 기획 제안서 등 문서 보관
│   ├── Prompt.txt
│   └── Startup Agent Web Proposal.docx
│
├── app/                           # 애플리케이션 코어 모듈
│   ├── __init__.py
│   ├── database.py                # SQLite DB 스키마 정의 및 데이터 조작
│   ├── valuation.py               # 하이브리드 권리금 감정평가 공식 구현
│   ├── scraper.py                 # 프랜차이즈 및 실시간 점포 정보 스크래핑 모킹
│   ├── rag.py                     # 벡터 검색 및 RAG 기반 AI 챗봇 엔진
│   └── utils.py                   # OCR 서류 추출 및 국세청 진위확인 API
│
├── main.py                        # Streamlit 통합 메인 엔트리포인트
├── readme.md                      # 총괄 에이전트 명세서
├── design.md                      # 디자이너 에이전트 가이드
└── dev.md                         # 본 개발 기술 명세서
```

---

## 3. 핵심 수식 구현 스펙

### 3.1. 유형자산 감가상각 (원가법) 공식
인테리어 및 시설의 잔존가치 $V_f$는 다음 공식을 따른다:
$$V_f = P \times \left(1 - \frac{t}{60}\right) \times C_q$$
*   $P$: 최초 설치 재조달원가
*   $t$: 경과 운영 월수 (최대 60개월 상한선 설정)
*   $C_q$: 설비 보존 정성 보정 계수 ($0.0 \sim 1.0$)

### 3.2. 무형자산 가치 평가 (수익환원법) 공식
브랜드, 단골 고객, 인지도 등 영업권리금 $V_i$는 미래 순 영업이익의 현재가치 환원 모형을 따른다:
$$V_i = \sum_{k=1}^N \frac{R_e}{(1 + R)^k}$$
*   $R_e$: 연간 자가인건비 차감 후 순 영업이익 (Card 매출 - 월세/인건비/기타 세법 경비)
*   $R$: 가이드라인 할인율 (기본값: $10\%$, 즉 $0.1$)
*   $N$: 영업가치 전이 유효 년수 (기본값: $2 \sim 5$년)

### 3.3. 총 권리금 산출 공식
$$V_{total} = V_f + V_i + V_l + V_a$$
*   $V_f$: 감가상각 반영 후 잔존 시설가치
*   $V_i$: 수익 환원 영업가치
*   $V_l$: 주변 비교 실거래 기반 바닥 권리금
*   $V_a$: 행정 인허가 권리 평가액

---

## 4. 데이터베이스 DDL 명세

SQLite 데이터베이스 세팅을 위한 DDL SQL 구문입니다.

```sql
-- 1. Users Table
CREATE TABLE IF NOT EXISTS Users (
    user_uuid TEXT PRIMARY KEY,
    auth_phone TEXT UNIQUE NOT NULL,
    user_role TEXT NOT NULL CHECK(user_role IN ('SELLER', 'BUYER', 'HQ_ADMIN')),
    registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. StoreProperties Table
CREATE TABLE IF NOT EXISTS StoreProperties (
    store_uuid TEXT PRIMARY KEY,
    owner_uuid TEXT,
    biz_reg_no TEXT UNIQUE NOT NULL,
    store_brand TEXT NOT NULL,
    established_date TEXT NOT NULL,
    address_detail TEXT NOT NULL,
    verification_status TEXT DEFAULT 'PENDING' CHECK(verification_status IN ('PENDING', 'REAL_VALID', 'BLOCKED_FAKE')),
    FOREIGN KEY(owner_uuid) REFERENCES Users(user_uuid)
);

-- 3. Valuations Table
CREATE TABLE IF NOT EXISTS Valuations (
    valuation_id INTEGER PRIMARY KEY AUTOINCREMENT,
    store_uuid TEXT,
    val_facility REAL NOT NULL DEFAULT 0.0,
    val_operating REAL NOT NULL DEFAULT 0.0,
    val_location REAL NOT NULL DEFAULT 0.0,
    val_license REAL NOT NULL DEFAULT 0.0,
    calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(store_uuid) REFERENCES StoreProperties(store_uuid)
);
```

---

## 5. RAG (Retrieval-Augmented Generation) & Chatbot 로직
1.  **벡터 데이터 생성**: 공정거래위원회 표준 프랜차이즈 가이드라인 및 국토부 상가임대차 권리금 표준 계약서 텍스트를 문장 단위로 분할하여 로컬 벡터 스토어에 저장.
2.  **유사도 검색**: 사용자 질문 입력 시, `SentenceTransformer` 모델을 통해 질문 벡터를 생성하고 문서 벡터들과 코사인 유사도를 계산하여 상위 $K$개 조각 검색.
3.  **컨텍스트 제공 및 챗봇 답변**: 검색된 문서 내용 조각을 LLM Prompt에 Context로 주입하여 법률 및 실무에 맞는 점포 양도양수 가이드를 생성하여 답변.

# 점포창업(양도양수) 도우미 에이전트 (Store Start-up & Transfer Assistance Agent)

본 프로젝트는 개인 및 프랜차이즈 점포 거래 시장의 정보 비대칭성을 해소하고, 허위 매물 및 계약 사기를 방지하기 위해 구축된 인공지능 기반 점포 양도양수 및 가맹 창업 통합 에이전트 플랫폼입니다.

---

## 1. 시스템 아키텍처 및 데이터 흐름

플랫폼은 크게 **예비 창업자(Buyer) 지원 프로세스**, **매도 점주(Seller) 매물 등록 및 검증 프로세스**, 그리고 **프랜차이즈 본사(HQ) 성장 솔루션**으로 구성됩니다.

```
                  ┌────────────────┐
                  │   매도 점주    │
                  └───────┬────────┘
                          │ (사업자등록증 & 점포 정보 등록)
                          ▼
             ┌─────────────────────────┐
             │ OCR & 국세청 진위 검증  │ ◀─── 국세청 상태조회 API
             └────────────┬────────────┘
                          │ (검증 완료 시 등록)
                          ▼
               ┌─────────────────────┐
               │  StoreProperties    │
               └──────────┬──────────┘
                          │
                          ▼
            ┌──────────────────────────┐
            │   하이브리드 권리평가    │ ◀─── 카드매출 API / 상권분석 API
            │ (유형 자산 + 무형 자산)  │
            └─────────────┬────────────┘
                          │
                          ▼
                ┌──────────────────┐
                │   Valuations     │
                └──────────┬───────┘
                           │
                           ▼
                 ┌──────────────────┐
                 │  Streamlit UI    │
                 └──────────▲───────┘
                            │
        ┌───────────────────┴───────────────────┐
        │                                       │
┌───────┴───────┐                       ┌───────┴───────┐
│ 예비 창업자   │                       │ 프랜차이즈 본사│
│ (챗봇, 매칭)  │                       │ (상권 분석)   │
└───────────────┘                       └───────────────┘
```

---

## 2. 데이터베이스 스키마 설계

물리 데이터 모델은 데이터 무결성과 투명성을 제공하기 위해 다음과 같이 구성됩니다.

### 2.1. 사용자 테이블 (`Users`)
사용자의 등급과 거래 역할을 분류하고 본인확인을 거친 계정 정보를 저장합니다.

| 필드명 | 데이터 타입 | 제약 조건 | 설명 |
| :--- | :--- | :--- | :--- |
| `user_uuid` | UUID | PRIMARY KEY, DEFAULT gen_random_uuid() | 사용자 시스템 고유 식별자 |
| `auth_phone` | VARCHAR(15) | UNIQUE, NOT NULL | 휴대폰 본인 인증 검증 완료 전화번호 |
| `user_role` | VARCHAR(20) | NOT NULL, CHECK (IN ('SELLER', 'BUYER', 'HQ_ADMIN')) | 매도점주, 예비창업인, 가맹본사 지배 계정 분할 |
| `registered_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | 가입 일자 및 계정 활성화 일자 |

### 2.2. 점포 매물 정보 테이블 (`StoreProperties`)
진위 증빙 및 공공 데이터 대조가 완료된 오프라인 거래 대상 마스터 테이블입니다.

| 필드명 | 데이터 타입 | 제약 조건 | 설명 |
| :--- | :--- | :--- | :--- |
| `store_uuid` | UUID | PRIMARY KEY | 매물 등록 관리 시스템 ID |
| `owner_uuid` | UUID | FOREIGN KEY REFERENCES Users(user_uuid) | 해당 매물을 매각하는 매도자 ID |
| `biz_reg_no` | VARCHAR(10) | UNIQUE, NOT NULL | 공공 원장 대조가 완료된 국세청 등록 사업자번호 |
| `store_brand` | VARCHAR(100) | NOT NULL | 정식 상호명 및 대상 가맹 브랜드 가입 명칭 |
| `established_date` | DATE | NOT NULL | 사업자등록상 실개업 연월일 |
| `address_detail` | TEXT | NOT NULL | 물리 지리적 확인이 보장되는 등기 주소 |
| `verification_status`| VARCHAR(20) | DEFAULT 'PENDING' | 검증 진행 상황 (PENDING, REAL_VALID, BLOCKED_FAKE) |

### 2.3. 정량 권리 평가 테이블 (`Valuations`)
플랫폼의 하이브리드 계산 알고리즘을 통해 계량 정산된 세부 가치 평가 내역을 보관합니다.

| 필드명 | 데이터 타입 | 제약 조건 | 설명 |
| :--- | :--- | :--- | :--- |
| `valuation_id` | BIGINT | PRIMARY KEY, GENERATED ALWAYS AS IDENTITY | 감정평가 결과 고유 관리 번호 |
| `store_uuid` | UUID | FOREIGN KEY REFERENCES StoreProperties(store_uuid) | 평가가 실행된 대상 물리 매물 코드 |
| `val_facility` | NUMERIC(15,2) | NOT NULL, DEFAULT 0 | 60개월 감가상각 시설 정산 권리 잔존액 (원가법) |
| `val_operating` | NUMERIC(15,2) | NOT NULL, DEFAULT 0 | 미래 순영업이익 수익가치 기반 계산 영업권액 (수익환원법) |
| `val_location` | NUMERIC(15,2) | NOT NULL, DEFAULT 0 | 노변 유사 실거래 비교 바닥 위치 권리 가치 산출액 |
| `val_license` | NUMERIC(15,2) | NOT NULL, DEFAULT 0 | 특수 인허가 권장 시장 보상 평가 산출금액 |
| `calculated_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | 알고리즘 구동 평가 일자 및 갱신 시각 |

---

## 3. 설치 및 실행 가이드

### 3.1. 가상환경 활성화
```powershell
# Windows PowerShell
.\.venv\Scripts\Activate.ps1
```

### 3.2. 종속성 설치
```bash
pip install -r requirements.txt
```

### 3.3. 프로그램 구동
```bash
streamlit run main.py
```

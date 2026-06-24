# 개발자 Agent (dev.md)

이 파일은 **퀀트투자 포트폴리오 웹 애플리케이션**의 개발 아키텍처, 데이터 파이프라인, 데이터베이스 테이블 스펙 및 구현 지침을 관리하는 문서입니다. 구조 수정이나 코드 변경 작업 시 최우선으로 참고합니다.

---

## 🛠️ 기술 스택 (Tech Stack)
- **Programming Language**: Python 3.8+
- **Web UI Framework**: Streamlit
- **Database Management**: MySQL 8.x
- **DB Connection Library**: `pymysql`, `SQLAlchemy` (엔진 기반 연결)
- **Data Processing**: `pandas`, `numpy`
- **Finance API**: `yfinance`, `yahooquery`
- **Portfolio Optimization**: `riskfolio-lib` (충돌 방지를 위해 `v3.3.0` 권장)
- **Data Visualization**: `plotly`, `matplotlib`, `seaborn`

---

## 💾 데이터베이스 스키마 및 테이블 정보

데이터베이스 명은 `stock_db`를 사용하며 주요 테이블은 다음과 같습니다. 상세 SQL 정의는 `테이블생성.sql`을 참조하십시오.

### 1. `kor_ticker` (기초 티커 정보)
- 주식 종목의 기본 명칭, 코드, 시가총액, BPS, EPS 등의 스냅샷 정보를 보관합니다.
- **Key Columns**: `종목코드` (varchar(6)), `종목명` (varchar(20)), `시가총액` (float), `기준일` (date)

### 2. `kor_price` (일별 가격 데이터)
- 주가의 시가, 고가, 저가, 종가 및 거래량을 저장합니다.
- **Key Columns**: `날짜` (date), `종가` (double), `거래량` (double), `종목코드` (varchar(6))

### 3. `kor_fs` (재무제표 원본 데이터)
- 기업 공시 구분에 따른 재무제표 계정과 값들을 관리합니다.
- **Key Columns**: `계정` (varchar(30)), `기준일` (date), `값` (float), `종목코드` (varchar(6)), `공시구분` (varchar(1))

### 4. `kor_multi_factor` (최종 팩터 연산 결과)
- QVM(Quality, Value, Momentum) 종합 연산 결과를 반영하여 실 투자 대상(`invest = 'Y'`)을 식별하는 테이블입니다.
- **Key Columns**: `종목코드`, `z_quality`, `z_value`, `z_momentum`, `qvm`, `invest` (char(1))

---

## 🔄 데이터 수집 및 가공 파이프라인 실행 순서

아래 순서대로 데이터 크롤링 및 파이프라인 파일이 실행되어야 정상적으로 테이블이 갱신됩니다.

1. **`1.KOR_TICKER&SECTOR.py`**: 티커 리스트 및 업종 정보 갱신
2. **`2.KOR_PRICE.py`**: 개별 종목 일별 가격 데이터 적재
3. **`3.KOR_FS&VALUE.py`**: 재무제표 정보 수집 및 지표 계산
4. **`4.KOR_VALUE(공시구분 y).py`**: 연도별 공시 정보 처리 및 적재
5. **`5.kor_fs_value.py`**: 최종 재무제표 팩터 연산 완료 및 DB 이관

---

## 💻 코드 구현 및 최적화 가이드라인

### 1. 환경 변수 및 보안
- 데이터베이스 비밀번호 및 민감한 접속 정보는 절대 코드에 하드코딩하지 않습니다.
- 프로젝트 루트 디렉토리에 `.env` 파일을 생성하고 `dotenv` 패키지를 통해 환경 변수를 로드합니다.
  ```properties
  DB_USER=root
  DB_PASSWORD=1234
  DB_HOST=127.0.0.1
  DB_PORT=3306
  DB_NAME=stock_db
  ```

### 2. Streamlit 캐싱 관리
- 로컬 DB 쿼리 실행 결과는 성능 극대화를 위해 `@st.cache_data`를 활용합니다.
- 캐시 키는 `max(기준일)` 또는 쿼리 조건 값을 파라미터로 넘겨 데이터가 업데이트되었을 때만 재쿼리하도록 구성합니다.
  ```python
  @st.cache_data
  def load_data(query):
      # DB 연결 및 데이터 로드 로직
      return df
  ```

### 3. 예외 및 결측치(NaN) 처리
- Pandas 연산 과정에서 발생하는 `np.nan` 값은 DB 적재 시 오류의 주원인이 되므로, `df.replace({np.nan: None})` 처리를 거친 후 삽입(to_sql)합니다.
- API 호출(yfinance, yahooquery) 시 트래픽 제한이나 일시적 오류를 방지하기 위해 `try-except` 예외 처리와 `time.sleep` 대기 시간 조율을 철저히 진행합니다.

---

## 🛠️ 기술적 개선 사양 구현 가이드 (Ch 11, 15, 16, 17 기반)

### 1. 해외 데이터 연동 (yfinance / yahooquery)
- **대상**: 미국 시장 시가총액 상위 종목 (예: AAPL, MSFT, GOOGL 등).
- **구현**: `yfinance` 및 `yahooquery`의 `Ticker` 객체를 이용하여 재무제표 및 가격 정보를 가져옵니다. 수집한 글로벌 데이터는 `global_ticker` 및 `global_multi_factor` 테이블에 별도로 구분하여 적재합니다.

### 2. 기술적 지표 계산 로직 모듈화
- **대상**: 이동평균선(SMA), 볼린저 밴드(Bollinger Bands), RSI(상대강도지수).
- **구현**:
  - `SMA = price.rolling(window=N).mean()`
  - `Bollinger Upper/Lower = SMA +/- (K * price.rolling(window=N).std())`
  - `RSI = 100 - (100 / (1 + RS))` (RS = 평균 상승분 / 평균 하락분)
  - 연산 코드는 `utils/quant_helper.py` 내 독립 함수로 모듈화하여 캐싱 처리합니다.

### 3. 주기적 리밸런싱 백테스터 구현
- **대상**: 분기별/월별 포트폴리오 리밸런싱.
- **구현**:
  - 리밸런싱 주기(일 수)마다 QVM 랭킹 상위 20 종목을 재선정합니다.
  - 리밸런싱 거래 발생 시, 거래세 및 매매수수료(예: 편도 0.25% 수준) 및 슬리피지(Slippage)를 자산 잔고에서 차감 계산합니다.

### 4. 증권사 API 연동 가상 주문 신호 생성
- **대상**: 주문 템플릿 생성 및 한국투자증권 API 구조 대응.
- **구현**:
  - 스크리닝 결과 종목들의 목표 자산 배분 비중(Weights)과 현재 보유 수량을 대입하여 필요한 주문 수량을 계산합니다.
  - 주문 형식에 최적화된 CSV 신호 테이블을 내보내는 기능을 UI에 제공합니다.


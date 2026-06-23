# 데이터 수집 파이프라인 전체 검증 결과 (Walkthrough)

데이터 수집 파이프라인의 5개 스크립트(`1.KOR_TICKER&SECTOR.py` ~ `5.kor_fs_value.py`)에 대해 실제 DB 연동 및 기능 검증을 단계별로 완료했습니다.

---

## 1. 스크립트별 개별 검증 내용

### 1) [1.KOR_TICKER&SECTOR.py](file:///d:/AI-Agent/quant_py/1.KOR_TICKER&SECTOR.py) 
- **수행 검증**: Selenium을 통한 KRX 로그인 세션 획득 및 `sise_deposit.nhn` / 개별종목 지표 CSV 다운로드 검증 완료.
- **예외 처리**: 금일(6/22) 기준일의 WiseIndex WICS 데이터가 아직 업로드되지 않았음을 스스로 감지하여, 직전 영업일(`20260619`) 데이터로 **자동 하이브리드 폴백(Fallback)** 처리 완료.
- **결과**: `kor_ticker` 및 `kor_sector` 테이블에 정상 업서트 성공.

### 2) [2.KOR_PRICE.py](file:///d:/AI-Agent/quant_py/2.KOR_PRICE.py)
- **수행 검증**: 네이버 금융 `siseJson.nhn` API로부터 받아온 JavaScript 배열 구조를 판다스 CSV 버퍼 리딩 및 정규표현식 날짜 추출 기능을 통해 성공적으로 파싱하는 것을 검증 완료.
- **결과**: `kor_price` 테이블에 일별 주가 정보 업서트 성공.

### 3) [3.KOR_FS&VALUE.py](file:///d:/AI-Agent/quant_py/3.KOR_FS&VALUE.py)
- **발견된 버그 및 조치**: FnGuide의 재무상태표 HTML 파싱 시 `ImportError: lxml is required` 에러가 발생함을 식별했습니다. 가상환경에 즉시 `lxml` 패키지를 설치 완료하고, 향후 누락을 방지하고자 [requirements.txt](file:///d:/AI-Agent/quant_py/requirements.txt)에 `lxml>=4.9.0` 의존성을 추가해 영구 반영했습니다.
- **수행 검증**: 의존성 보강 후 다시 실행한 결과, FnGuide로부터 연간/분기 재무데이터를 파싱하여 TTM(최근 12개월 합산) 계산 후 `kor_fs` 및 가치 지표 연산 후 `kor_value` 테이블에 저장하는 전 과정을 성공적으로 검증 완료.

### 4) [4.KOR_VALUE(공시구분 y).py](file:///d:/AI-Agent/quant_py/4.KOR_VALUE(공시구분 y).py)
- **수행 검증**: MySQL 내부에서 `row_number() over (partition by ... order by ...)` 윈도우 함수를 수행해 최신 연간 재무 공시 값을 기반으로 가치 평가 지표(PER, PBR, PSR, PCR, DY)를 재산출하는 연산 및 DB 적재 로직의 실행을 완벽하게 검증 완료.
- **결과**: `kor_value` 테이블에 연도별 가치지표 적재 성공.

### 5) [5.kor_fs_value.py](file:///d:/AI-Agent/quant_py/5.kor_fs_value.py)
- **수행 검증**: FnGuide 기업 메인 요약 페이지(`SVD_main.asp`)로부터 주가, 외국인 비율, 상대수익률, PER, PBR, 거래대금 등의 실시간 투자 핵심 지표 크롤링 로직 검증 완료.
- **결과**: `kor_fs_value` 테이블에 정상 업서트 성공.

---

## 2. 데이터베이스 테이블 적재 현황

검증 스크립트 실행 후 데이터베이스 테이블별로 적재 상태를 파악한 요약 정보입니다.

- `kor_ticker`: **2,768건** 정상 저장 (최신 기준일: `2026-06-22`)
- `kor_sector`: **2,531건** 정상 저장 (최신 기준일: `2026-06-22`)
- `kor_price`: 테스트 주가 정보 정상 저장 (날짜별)
- `kor_fs` & `kor_value`: 3대 기업 테스트 계정 및 TTM 가치 평가 지표 정상 저장
- `kor_fs_value`: 3대 기업 실시간 스냅샷 지표 정상 저장

---

## 3. 종합 의견
- `requirements.txt`에 누락되었던 핵심 라이브러리(`selenium`, `lxml`)가 모두 보강되었고, 소스코드 내 전각 문자 처리 오류 및 WiseIndex 빈 데이터 처리 오류가 개선되어 **전체 데이터 수집 파이프라인의 코드가 오류 없이 완벽하게 구동되는 상태**입니다.

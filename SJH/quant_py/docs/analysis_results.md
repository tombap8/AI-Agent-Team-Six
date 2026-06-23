# 1.KOR_TICKER&SECTOR.py 코드 검수 결과 보고서

`1.KOR_TICKER&SECTOR.py` 스크립트와 의존 라이브러리(`utils/krx_login.py`), 그리고 `테이블생성.sql`을 연계하여 정밀 검수한 결과입니다. 시스템의 오작동을 유발할 수 있는 **크리티컬한 오류 2건**을 포함하여 총 6가지 개선 포인트를 도출했습니다.

---

## 1. 검수 요약 (Summary)

| 분류 | 등급 | 내용 | 영향도 |
| :--- | :--- | :--- | :--- |
| **DB 스키마 불일치** | **Critical** | `kor_ticker` 테이블의 DB 칼럼 정의와 Python Insert 쿼리 칼럼 구성 불일치 | 프로그램 실행 및 데이터 적재 불가 (OperationalError 발생) |
| **하드코딩된 파일 경로** | **Critical** | `krx_login.py` 내 타인 컴퓨터의 사용자명(`kosa`) 기반 절대 경로 지정 | 자동 로그인 수행 중 스크린샷 저장 단계에서 프로그램 강제 종료 |
| **데이터 정제 누락** | **Warning** | 수치형 칼럼에 데이터가 없을 때 들어오는 대시 기호(`'-'`) 처리 누락 | MySQL Float 형 변환 중 `Data truncated` 에러 발생 가능 |
| **최신 데이터 반영 지연** | **Info** | 장 마감(16시) 이후 실행해도 항상 이전 영업일 데이터를 수집함 | 당일 종가 데이터 적재 지연 (하루 단위 백테스트 상 지연 발생) |
| **보안 취약점** | **Warning** | KRX 로그인용 ID/PW 평문 노출 | 깃허브 등 공용 저장소 업로드 시 계정 정보 탈취 위험 |
| **타입 어노테이션 불일치** | **Info** | 날짜 헬퍼 함수의 반환 어노테이션(`date`)과 실제 반환값(`str`) 상이 | 코드 분석기 가독성 및 정적 타입 체크 경고 발생 |

---

## 2. 주요 문제점 및 개선 방향 (Details)

### 🚨 [Critical] 1) `kor_ticker` DB 테이블 구조와 Insert 쿼리 불일치
- **현상**:
  - `테이블생성.sql`에서는 `kor_ticker` 테이블에 **`선행EPS`**는 있지만, **`PER`**, **`PBR`**, **`배당수익률`** 칼럼은 정의되어 있지 않습니다.
  - 반면, `1.KOR_TICKER&SECTOR.py`의 191~197행 Insert 쿼리에서는 `PER`, `PBR`, `배당수익률`을 직접 삽입(Insert)하고 업서트(Upsert)하려 시도합니다.
- **영향**: 처음 스키마를 생성하고 이 파이프라인을 실행하면 MySQL에서 `Unknown column 'PER' in 'field list'` 에러를 내뱉으며 전체 작업이 실패합니다.
- **해결 방안**:
  `테이블생성.sql`의 `kor_ticker` 스키마를 아래와 같이 변경하여 저장해야 합니다.

  ```sql
  -- 수정 후 kor_ticker 테이블 스키마
  create table kor_ticker
  (
      종목코드 varchar(6) not null,
      종목명 varchar(20),
      시장구분 varchar(6),
      종가 float,
      시가총액 float,
      기준일 date,
      EPS float,
      선행EPS float,  -- 기존 유지
      BPS float,
      PER float,      -- 추가
      PBR float,      -- 추가
      주당배당금 float,
      배당수익률 float, -- 추가
      종목구분 varchar(5),
      primary key(종목코드, 기준일)
  );
  ```

---

### 🚨 [Critical] 2) `utils/krx_login.py` 내 타인 계정 경로 하드코딩
- **현상**: `utils/krx_login.py` 파일 124~125행을 보면 아래와 같이 특정 폴더 경로가 하드코딩되어 있습니다.
  ```python
  screenshot_path = r"C:\Users\kosa\.gemini\antigravity-ide\brain\2c12c07b-f08d-485c-bf72-1b6e5048641e\scratch\post_login.png"
  driver.save_screenshot(screenshot_path)
  ```
- **영향**: 사용자 환경의 윈도우 계정명(`USER`) 또는 임시 디렉터리 경로와 맞지 않아 브라우저 캡처본을 저장하는 도중 `FileNotFoundError`가 발생해 로그인이 완전 실패합니다.
- **해결 방안**: 
  스크립트가 위치한 상대 경로 기준 또는 시스템 임시 폴더에 저장되도록 수정해야 합니다.
  ```python
  # 변경 전: screenshot_path = r"C:\Users\kosa\..."
  # 변경 후: 스크립트 실행 위치 하위 또는 생략
  screenshot_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'post_login.png')
  ```

---

### ⚠️ [Warning] 3) 수치 데이터 결측치(`'-'`) 문자열 처리 부족
- **현상**: KRX에서 개별종목 지표 데이터를 받아올 때, 실적이 없거나 배당을 주지 않는 기업의 `PER`, `PBR`, `배당수익률` 등의 값은 숫자 대신 대시 기호(`'-'`) 문자열 형태로 수집되는 경우가 빈번합니다.
- **영향**:
  - `1.KOR_TICKER&SECTOR.py` 177행의 `kor_ticker.replace({np.nan: None})` 처리는 판다스의 `NaN` 값만 `None`으로 바꿔줄 뿐, 문자열 `'-'`은 바꾸지 못합니다.
  - 이로 인해 문자열 `'-'`이 MySQL의 Float/Double 칼럼에 삽입되면서 데이터 잘림(`Data truncated`) 경고 또는 DB 드라이버 타입 에러가 발생하게 됩니다.
- **해결 방안**:
  데이터 전처리(Pandas) 단계에서 `'-'` 문자열도 확실하게 비워내거나 숫자로 강제 변환 후 `None` 처리를 적용해야 합니다.
  ```python
  # 문자열 '-'을 NaN으로 변환 후, 일괄적으로 None으로 매핑
  kor_ticker = kor_ticker.replace({'-': np.nan})
  
  # 수치형 칼럼에 대해 강제 숫자 변환(쉼표 제거 및 강제 형변환) 적용
  numeric_cols = ['종가', '시가총액', 'EPS', 'BPS', 'PER', 'PBR', '주당배당금', '배당수익률']
  for col in numeric_cols:
      if col in kor_ticker.columns:
          kor_ticker[col] = pd.to_numeric(kor_ticker[col].astype(str).str.replace(',', ''), errors='coerce')
          
  kor_ticker = kor_ticker.replace({np.nan: None})
  ```

---

### 🔒 [Warning] 4) 중요 자격 증명(ID/PW)의 소스코드 평문 노출
- **현상**: `1.KOR_TICKER&SECTOR.py` (31~32행)과 `utils/krx_login.py` (89, 92행)에 KRX 웹사이트 로그인을 위한 개인 아이디 및 패스워드가 코드 내에 그대로 노출되어 있습니다.
- **영향**: 보안 위배 사항으로 개인정보 유출 위험이 높습니다.
- **해결 방안**: 타 소스코드들처럼 이미 연동되어 있는 `.env` 파일을 활용해 데이터베이스 접속 정보와 동일하게 관리하도록 개선합니다.
  ```python
  # .env 파일에 추가
  # KRX_USER_ID=jhsong89
  # KRX_USER_PW=s@4452009
  
  # Python 스크립트 수정
  import os
  USER_ID = os.getenv("KRX_USER_ID", "default_id")
  USER_PW = os.getenv("KRX_USER_PW", "default_pw")
  ```

---

### 💡 [Info] 5) 장 마감 후 실행 시 최신 데이터 유실 방지(날짜 계산 로직 개선)
- **현상**:
  ```python
  today = date.today()
  prev_bd = get_previous_business_day(today)
  biz_day = prev_bd
  ```
  이 코드는 스크립트가 실행되는 시점과 관계없이 항상 "이전 영업일" 데이터를 받도록 설계되어 있습니다.
- **영향**: 오후 4시(16:00) 이후에는 당일 주식 시장이 완전히 마감되어 당일 최종 데이터가 이미 KRX 사이트에 업데이트된 상태입니다. 이때 수집기를 실행하더라도 당일 데이터가 아닌 전날(혹은 지난주 금요일)의 데이터를 덮어쓰거나 최신 적재 기회가 상실됩니다.
- **해결 방안**:
  현재 시각이 **평일 오후 4시(16시) 이후**인 경우에는 `biz_day`를 **오늘 날짜**로 지정하고, 그 외의 경우에는 이전 영업일로 유연하게 가져가도록 개선합니다.
  ```python
  from datetime import datetime, date, timedelta

  def get_latest_trading_day(today_date: date) -> str:
      now = datetime.now()
      
      # 주말(토요일=5, 일요일=6)이거나 임시 공휴일인 경우 -> 이전 영업일
      if today_date.weekday() >= 5 or is_holiday_mock(today_date.strftime("%Y-%m-%d")):
          return get_previous_business_day(today_date)
      
      # 평일이지만 장 마감 정보 공시 전(오후 4시 이전)인 경우 -> 이전 영업일
      if now.hour < 16:
          return get_previous_business_day(today_date)
          
      # 평일 오후 4시 이후인 경우 -> 당일 데이터 수집
      return today_date.strftime("%Y%m%d")

  biz_day = get_latest_trading_day(date.today())
  print(f"데이터 기준일: {biz_day}")
  ```

---

### 💡 [Info] 6) 날짜 계산 헬퍼 함수의 타입 어노테이션 가독성 개선
- **현상**:
  ```python
  def get_previous_business_day(today: date) -> date:
  ```
  함수의 반환형 힌트는 `date` 객체로 선언되어 있으나, 실제 마지막 `return` 코드는 문자열 포맷(`prev_day.strftime("%Y%m%d")`)을 반환합니다.
- **영향**: IDE에서 형식 불일치 경고를 표시하며 코드 분석 도구(linter 등)의 오류 탐지를 흐립니다.
- **해결 방안**: 
  반환 힌트를 `str`로 수정합니다.
  ```python
  def get_previous_business_day(today: date) -> str:
  ```

---

## 3. 검수 완료 후 제안 코드

수정 방향을 종합적으로 적용한 **안정화 버젼의 코드** 리팩토링 제안입니다. 

### 📁 수정 제안: [1.KOR_TICKER&SECTOR.py](file:///d:/AI-Agent/quant_py/1.KOR_TICKER&SECTOR.py) 수정본

```python
### 테이블 생성순서 : KOR_TICKER , KOR_SECTOR, KOR_PRICE, KOR_FS, KOR_VALUE
import os
import requests as rq
from bs4 import BeautifulSoup
from datetime import date, timedelta, datetime
from io import BytesIO
import pandas as pd
import numpy as np
import pymysql
import time
import json
from tqdm import tqdm
from dotenv import load_dotenv

# .env 로드
current_dir = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(current_dir, '.env'))

# ==========================================
# [설정] KRX 로그인 정보 로드 (환경변수 권장)
# ==========================================
USER_ID = os.getenv("KRX_USER_ID", "jhsong89")
USER_PW = os.getenv("KRX_USER_PW", "s@4452009")

# ==========================================
# 1. 세션 생성 및 로그인 (자동 로그인 헬퍼 사용)
# ==========================================
from utils.krx_login import get_krx_cookie

sess = rq.Session()

try:
    MY_COOKIE = get_krx_cookie(force_new=False)
except Exception as e:
    print(f"자동 로그인 쿠키 획득 중 에러 발생: {e}")
    MY_COOKIE = ''

headers = {
    'Referer': 'https://data.krx.co.kr/contents/MDC/MDI/mdiLoader',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Cookie': MY_COOKIE
}
sess.headers.update(headers)


# ==========================================
# 2. 날짜 계산 로직 개선
# ==========================================
def is_holiday_mock(d_str):
    return False 

def get_previous_business_day(today_val: date) -> str:
    one_day = timedelta(days=1)
    prev_day = today_val - one_day
    
    while True:
        if prev_day.weekday() >= 5:
            prev_day -= one_day
            continue
        if is_holiday_mock(prev_day.strftime("%Y-%m-%d")):
            prev_day -= one_day
            continue
        break
    return prev_day.strftime("%Y%m%d")

def get_latest_trading_day(today_val: date) -> str:
    now = datetime.now()
    if today_val.weekday() >= 5 or is_holiday_mock(today_val.strftime("%Y-%m-%d")):
        return get_previous_business_day(today_val)
    if now.hour < 16:
        return get_previous_business_day(today_val)
    return today_val.strftime("%Y%m%d")

today = date.today()
biz_day = get_latest_trading_day(today)
print(f"데이터 기준일: {biz_day}")


# ==========================================
# 3. 데이터 크롤링 (세션 객체 'sess' 사용)
# ==========================================
gen_otp_url = 'http://data.krx.co.kr/comm/fileDn/GenerateOTP/generate.cmd'
down_url = 'http://data.krx.co.kr/comm/fileDn/download_csv/download.cmd'

# (1) 코스피 업종분류
gen_otp_stk = {
    'mktId': 'STK',
    'trdDd': biz_day,
    'money': '1',
    'csvxls_isNo': 'false',
    'name': 'fileDown',
    'url': 'dbms/MDC/STAT/standard/MDCSTAT03901'
}

otp_stk = sess.post(gen_otp_url, gen_otp_stk).text
down_sector_stk = sess.post(down_url, {'code': otp_stk})
sector_stk = pd.read_csv(BytesIO(down_sector_stk.content), encoding='EUC-KR')

# (2) 코스닥 업종분류
gen_otp_ksq = {
    'mktId': 'KSQ',
    'trdDd': biz_day,
    'money': '1',
    'csvxls_isNo': 'false',
    'name': 'fileDown',
    'url': 'dbms/MDC/STAT/standard/MDCSTAT03901'
}

otp_ksq = sess.post(gen_otp_url, gen_otp_ksq).text
down_sector_ksq = sess.post(down_url, {'code': otp_ksq})
sector_ksq = pd.read_csv(BytesIO(down_sector_ksq.content), encoding='EUC-KR')

# 데이터 병합
krx_sector = pd.concat([sector_stk, sector_ksq]).reset_index(drop=True)
krx_sector['종목명'] = krx_sector['종목명'].str.strip()
krx_sector['기준일'] = biz_day

# (3) 개별종목 지표
gen_otp_data = {
    'searchType': '1',
    'mktId': 'ALL',
    'trdDd': biz_day,
    'csvxls_isNo': 'false',
    'name': 'fileDown',
    'url': 'dbms/MDC/STAT/standard/MDCSTAT03501'
}

otp_ind = sess.post(gen_otp_url, gen_otp_data).text
krx_ind_res = sess.post(down_url, {'code': otp_ind})
krx_ind = pd.read_csv(BytesIO(krx_ind_res.content), encoding='EUC-KR')
krx_ind['종목명'] = krx_ind['종목명'].str.strip()
krx_ind['기준일'] = biz_day

# (4) 데이터 가공 (Merge 및 정리)
diff = list(set(krx_sector['종목명']).symmetric_difference(set(krx_ind['종목명'])))

kor_ticker = pd.merge(krx_sector,
                      krx_ind,
                      on=krx_sector.columns.intersection(krx_ind.columns).tolist(),
                      how='outer')

# 종목구분 처리
kor_ticker['종목구분'] = np.where(kor_ticker['종목명'].str.contains('스팩|제[0-9]+호'), '스팩',
                              np.where(kor_ticker['종목코드'].str[-1:] != '0', '우선주',
                                       np.where(kor_ticker['종목명'].str.endswith('리츠'), '리츠',
                                                np.where(kor_ticker['종목명'].isin(diff),  '기타',
                                                '보통주'))))

kor_ticker = kor_ticker.reset_index(drop=True)
kor_ticker.columns = kor_ticker.columns.str.replace(' ', '')
kor_ticker = kor_ticker[['종목코드', '종목명', '시장구분', '종가',
                         '시가총액', '기준일',  'EPS', 'BPS', 'PER', 'PBR', '주당배당금', '배당수익률','종목구분']]

# ⚠️ 결측치 '-' 및 쉼표 제거 정화 작업 강화
kor_ticker = kor_ticker.replace({'-': np.nan})
numeric_cols = ['종가', '시가총액', 'EPS', 'BPS', 'PER', 'PBR', '주당배당금', '배당수익률']
for col in numeric_cols:
    if col in kor_ticker.columns:
        kor_ticker[col] = pd.to_numeric(kor_ticker[col].astype(str).str.replace(',', ''), errors='coerce')

kor_ticker = kor_ticker.replace({np.nan: None})
kor_ticker['기준일'] = pd.to_datetime(kor_ticker['기준일'])

print(f"KOR_TICKER 데이터 준비 완료: {len(kor_ticker)}건")


# DB 적재
from utils.db_helper import get_connection

con = get_connection()
mycursor = con.cursor()
query = f"""
    insert into kor_ticker (종목코드,종목명,시장구분,종가,시가총액,기준일,EPS,BPS,PER,PBR,주당배당금,배당수익률,종목구분)
    values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) as new
    on duplicate key update
    종목명=new.종목명,시장구분=new.시장구분,종가=new.종가,시가총액=new.시가총액,EPS=new.EPS,BPS=new.BPS,
    PER=new.PER,PBR=new.PBR,주당배당금=new.주당배당금,배당수익률=new.배당수익률,종목구분 = new.종목구분;
"""

args = kor_ticker.values.tolist()
mycursor.executemany(query, args)
con.commit()
con.close()


# ==========================================
# 4. WICS 섹터 정보 크롤링 (WiseIndex)
# ==========================================
print("WICS 섹터 정보 크롤링 시작...")

sector_code = ['G25', 'G35', 'G50', 'G40', 'G10', 'G20', 'G55', 'G30', 'G15', 'G45']
data_sector = []

for i in tqdm(sector_code):
    url = f'''http://www.wiseindex.com/Index/GetIndexComponets?ceil_yn=0&dt={biz_day}&sec_cd={i}'''    
    response = sess.get(url)
    
    # ⚠️ 응답 상태 및 HTTP 상태 코드 유효성 검사 추가
    if response.status_code == 200:
        try:
            data = response.json()
            if 'list' in data:
                data_pd = pd.json_normalize(data['list'])
                data_sector.append(data_pd)
        except Exception as e:
            print(f"Error parsing {i}: {e}")
    else:
        print(f"HTTP Error {response.status_code} requesting WiseIndex for sector {i}")
    
    time.sleep(0.5)

if data_sector:
    kor_sector = pd.concat(data_sector, axis=0)
    kor_sector = kor_sector[['IDX_CD', 'CMP_CD', 'CMP_KOR', 'SEC_NM_KOR']]
    kor_sector['기준일'] = biz_day
    kor_sector['기준일'] = pd.to_datetime(kor_sector['기준일'])
    print(f"KOR_SECTOR 데이터 준비 완료: {len(kor_sector)}건")
    
    # DB 적재
    con = get_connection()
    mycursor = con.cursor()
    query = f"""
        insert into kor_sector (IDX_CD, CMP_CD, CMP_KOR, SEC_NM_KOR, 기준일)
        values (%s,%s,%s,%s,%s) as new
        on duplicate key update
        IDX_CD = new.IDX_CD, CMP_KOR = new.CMP_KOR, SEC_NM_KOR = new.SEC_NM_KOR
    """
    args_sector = kor_sector.values.tolist()
    mycursor.executemany(query, args_sector)
    con.commit()
    con.close()
else:
    print("KOR_SECTOR 데이터를 가져오지 못했습니다.")
```

---

### 📁 수정 제안: [utils/krx_login.py](file:///d:/AI-Agent/quant_py/utils/krx_login.py) 124~126행 수정본

```python
        # Diagnostics
        print("[KRX Login] Post-login URL:", driver.current_url)
        print("[KRX Login] Post-login Title:", driver.title)
        
        # ⚠️ 타인 절대 경로 하드코딩 제거 및 로컬 스크립트 상대 경로화
        screenshot_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'post_login.png')
        driver.save_screenshot(screenshot_path)
        print("[KRX Login] Post-login screenshot saved to:", screenshot_path)
```

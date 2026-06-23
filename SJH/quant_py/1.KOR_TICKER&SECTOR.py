### 테이블 생성순서 : KOR_TICKER , KOR_SECTOR, KOR_PRICE, KOR_FS, KOR_VALUE
# KOR_TICKER	    7,972
# KOR_SECTOR	    7,323
# KOR_PRICE	2,704,313
# KOR_FS	   1,808,232
# KOR_VALUE	   21,318
#######################   KOR_TICKER     #######################
# 최근영업일 기준 데이터받기
# 국내증시 → 증시자금동향 : 이전 2영업일
# https://finance.naver.com/sise/sise_deposit.nhn
# KRX정보데이터시스템 [기본통계 > 주식 > 세부안내]
# [12025]업종분류현황(http://data.krx.co.kr/contents/MDC/MDI/mdiLoader/index.cmd?menuId=MDC0201020506) 크롤링
# [12021]개별종목(http://data.krx.co.kr/contents/MDC/MDI/mdiLoader/index.cmd?menuId=MDC0201020502) 크롤링
### 테이블 생성순서 : KOR_TICKER , KOR_SECTOR, KOR_PRICE, KOR_FS, KOR_VALUE
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
import os
from dotenv import load_dotenv
# holidayskr 패키지가 없다면 pip install holidayskr 필요
# from holidayskr import is_holiday # (사용자 환경에 맞게 주석 해제/설정)

# ==========================================
# [설정] KRX 로그인 정보 입력
# ==========================================
# .env 파일 로드 (부모 폴더 또는 현재 폴더)
current_dir = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(current_dir, '.env'))

USER_ID = os.getenv("KRX_USER_ID", "jhsong89")
USER_PW = os.getenv("KRX_USER_PW", "s@4452009")

# ==========================================
# ==========================================
# 1. 세션 생성 및 로그인 (자동 로그인 헬퍼 사용)
# ==========================================
from utils.krx_login import get_krx_cookie

# 세션을 생성하여 쿠키(로그인 정보)를 유지합니다.
sess = rq.Session()

# Selenium 헬퍼를 통해 유효한 세션 쿠키를 자동으로 획득합니다.
try:
    MY_COOKIE = get_krx_cookie(force_new=False)
except Exception as e:
    print(f"자동 로그인 쿠키 획득 중 에러 발생: {e}")
    # Fallback to empty if it fails
    MY_COOKIE = ''

headers = {
    'Referer': 'https://data.krx.co.kr/contents/MDC/MDI/mdiLoader',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Cookie': MY_COOKIE
}
sess.headers.update(headers)

    # 로그인이 필수라면 여기서 프로그램을 종료하거나 예외처리 필요


# ==========================================
# 2. 날짜 계산 로직 (개선)
# ==========================================
# 임시 함수: holidayskr 라이브러리가 없는 환경을 위해 간단한 휴일 체크 로직으로 대체 가능
def is_holiday_mock(d_str):
    # 실제 holidayskr 라이브러리가 있다면 from holidayskr import is_holiday 사용
    return False 

today = date.today()

def get_previous_business_day(today_val: date) -> str:
    one_day = timedelta(days=1)
    prev_day = today_val - one_day
    
    while True:
        # 주말(토=5, 일=6) 제외
        if prev_day.weekday() >= 5:
            prev_day -= one_day
            continue
        
        # 공휴일 제외 (여기서는 임시 함수 사용, 실제 환경에 맞게 수정)
        if is_holiday_mock(prev_day.strftime("%Y-%m-%d")):
            prev_day -= one_day
            continue
        
        break
    return prev_day.strftime("%Y%m%d")

def get_latest_trading_day(today_val: date) -> str:
    now = datetime.now()
    # 주말(토=5, 일=6)이거나 공휴일이면 이전 영업일
    if today_val.weekday() >= 5 or is_holiday_mock(today_val.strftime("%Y-%m-%d")):
        return get_previous_business_day(today_val)
    # 평일이지만 장 마감 정보 공시 전(오후 4시 이전)이면 이전 영업일
    if now.hour < 16:
        return get_previous_business_day(today_val)
    return today_val.strftime("%Y%m%d")

biz_day = get_latest_trading_day(today)
#biz_day = '20260430'
print(f"데이터 기준일: {biz_day}")


# ==========================================
# 3. 데이터 크롤링 (세션 객체 'sess' 사용)
# ==========================================

#######################   KOR_TICKER (업종분류 + 개별종목)   #######################

# 공통 URL
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

# sess.post를 사용하여 로그인된 상태로 요청
otp_stk = sess.post(gen_otp_url, gen_otp_stk).text
print("DEBUG: otp_stk =", repr(otp_stk))
down_sector_stk = sess.post(down_url, {'code': otp_stk})
print("DEBUG: down_sector_stk status =", down_sector_stk.status_code)
print("DEBUG: down_sector_stk preview =", repr(down_sector_stk.content[:200]))
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

# 결측치 '-' 및 쉼표 제거 정화 작업
kor_ticker = kor_ticker.replace({'-': np.nan})
numeric_cols = ['종가', '시가총액', 'EPS', 'BPS', 'PER', 'PBR', '주당배당금', '배당수익률']
for col in numeric_cols:
    if col in kor_ticker.columns:
        kor_ticker[col] = pd.to_numeric(kor_ticker[col].astype(str).str.replace(',', ''), errors='coerce')

kor_ticker = kor_ticker.replace({np.nan: None})
kor_ticker['기준일'] = pd.to_datetime(kor_ticker['기준일'])

print(f"KOR_TICKER 데이터 준비 완료: {len(kor_ticker)}건")

# DB 적재 로직 (기존과 동일)
# ... (pymysql 부분은 DB 접속 정보가 필요하므로 생략하거나 기존 코드 유지) ...
kor_ticker.head()

# 파이썬에서 아래 코드를 실행하면 다운로드 받은 정보가 kor_ticker 테이블에 upsert 형태로 저장
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

#######################   KOR_SECTOR (WICS)   #######################
# WiseIndex는 KRX와 다른 사이트이므로 로그인 세션 공유 불필요 (일반 requests 사용 가능하지만 sess 써도 무방)
print("WICS 섹터 정보 크롤링 시작...")

# WiseIndex는 금일 데이터가 장 마감 후에도 바로 업데이트되지 않는 경우가 많으므로,
# 만약 금일(biz_day) 데이터가 없다면 이전 영업일 데이터를 시도합니다.
wise_biz_day = biz_day
test_url = f'''http://www.wiseindex.com/Index/GetIndexComponets?ceil_yn=0&dt={biz_day}&sec_cd=G25'''
try:
    test_res = sess.get(test_url)
    if test_res.status_code == 200:
        test_data = test_res.json()
        if not test_data.get('list'):
            wise_biz_day = get_previous_business_day(today)
            print(f"WiseIndex에 오늘({biz_day}) 데이터가 아직 업로드되지 않았습니다. 이전 영업일({wise_biz_day}) 데이터를 가져옵니다.")
except Exception as e:
    print(f"WiseIndex 상태 확인 중 에러 발생: {e}")

sector_code = ['G25', 'G35', 'G50', 'G40', 'G10', 'G20', 'G55', 'G30', 'G15', 'G45']
data_sector = []

for i in tqdm(sector_code):
    url = f'''http://www.wiseindex.com/Index/GetIndexComponets?ceil_yn=0&dt={wise_biz_day}&sec_cd={i}'''    
    # WiseIndex는 별도 사이트이므로 그냥 rq.get 혹은 sess.get 사용
    # 단, WiseIndex가 JSON 응답을 주므로 .json() 처리
    response = sess.get(url)
    
    if response.status_code == 200:
        try:
            data = response.json()
            if 'list' in data and len(data['list']) > 0:
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
else:
    print("KOR_SECTOR 데이터를 가져오지 못했습니다.")


# DB 적재 로직 (기존 코드 유지)
# 파이썬에서 위 코드를 실행하면 다운로드 받은 정보가 kor_sector 테이블에 upsert 형태로 저장
from utils.db_helper import get_connection

con = get_connection()
mycursor = con.cursor()
query = f"""
    insert into kor_sector (IDX_CD, CMP_CD, CMP_KOR, SEC_NM_KOR, 기준일)
    values (%s,%s,%s,%s,%s) as new
    on duplicate key update
    IDX_CD = new.IDX_CD, CMP_KOR = new.CMP_KOR, SEC_NM_KOR = new.SEC_NM_KOR
"""

args = kor_sector.values.tolist()

mycursor.executemany(query, args)
con.commit()

con.close()
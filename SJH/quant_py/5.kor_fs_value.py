#######################   KOR_FS_VALUE (참조 : KOR_TICKER)   ####################
## 10.5 재무제표 크롤링
# http://comp.fnguide.com/
# 2.전종목 재무제표 크롤링
# 패키지 불러오기
import pymysql
from sqlalchemy import create_engine
import pandas as pd
import requests as rq
from bs4 import BeautifulSoup
import re
from tqdm import tqdm
import time
from urllib.request import urlopen
import datetime

def my_function(value):
  try:
    # 실수형으로 변환하고, 기본값 0을 설정
    value = float(value) or 0
  except ValueError:
    # 변환하지 못한 경우 처리
    pass
  # 이후 처리

def convert_to_float(s, default_value=0.0):
    try:
        return float(s)
    except ValueError:
        return default_value
    
#today = datetime.datetime.now()
# 현재일자 문자 8자리를 가져옵니다.
#today_str = today.strftime("%Y%m%d%H%M%S")
# 전영업일을 가져옵니다.
#prev_working_day = today - datetime.timedelta(days=1)
# 전영업일 문자 8자리를 가져옵니다.
#prev_working_day_str = prev_working_day.strftime("%Y%m%d")
#print(today_str)  # 20240126151356
#print(prev_working_day_str)

# DB 연결
from utils.db_helper import get_engine, get_connection

engine = get_engine()
con = get_connection()
mycursor = con.cursor()

# 티커리스트 불러오기
ticker_list = pd.read_sql("""
select * from kor_ticker
where 기준일 = (select max(기준일) from kor_ticker) 
 	and 종목구분 = '보통주';
""", con=engine)

# DB 저장 쿼리
query = """
    insert into kor_fs_value (종목코드, 종목명, 기준일, 주가, 외국인보유비중, 상대수익률, PER, PER_12M, 업종PER, PBR, DY, 거래량, 거래대금, 시가총액, 시가총액_보통주)
    values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) as new
    on duplicate key update
    주가 = new.주가, 외국인보유비중 = new.외국인보유비중, 상대수익률 = new.상대수익률, PER = new.PER, PER_12M = new.PER_12M, 업종PER = new.업종PER, PBR = new.PBR, 
    DY = new.DY, 거래량 = new.거래량, 거래대금 = new.거래대금, 시가총액 = new.시가총액, 시가총액_보통주 = new.시가총액_보통주 ;
"""

# 오류 발생시 저장할 리스트 생성
error_list = []

# for loop
for i in tqdm(range(0, len(ticker_list))):

    # 티커 선택
    ticker = ticker_list['종목코드'][i]

    # 오류 발생 시 이를 무시하고 다음 루프로 진행
    try:

        # url 생성
        url = f'http://comp.fnguide.com/SVO2/ASP/SVD_main.asp?pGB=1&gicode=A{ticker}'

        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
        req = rq.get(url, headers=headers)
        bs_obj = BeautifulSoup(req.content, "html.parser")

        # 날짜 
        date1 = bs_obj.find("span", {"class":"date"})
        date2 = date1.text
        date = date2.replace('[','').replace(']','').replace('/','-')

        # 기업정보
        corp_name1 = bs_obj.find_all("h1", {"id":"giName"})
        corp_name = corp_name1[0].text

        #종목코드
        code1 = bs_obj.find_all("div", {"class":"corp_group1"})
        code2 = code1[0].find("h2")
        code = code2.text

        #주가
        stock_price1 = bs_obj.find("span", {"id":"svdMainChartTxt11"})
        stock_price2 = stock_price1.text
        stock_price = int(stock_price2.replace(',', '').strip())

        #외국인 보유비중
        fgn_own_ratio1 = bs_obj.find("span", {"id":"svdMainChartTxt12"})
        fgn_own_ratio = float(fgn_own_ratio1.text)

        #상대수익률
        rel_return1 = bs_obj.find("span", {"id":"svdMainChartTxt13"})
        rel_return1 = rel_return1.text
        rel_return = convert_to_float(rel_return1, default_value=0.0)

        ### 상단리스트 
        up_list = bs_obj.find("div", {"class":"corp_group2"})
        dd = up_list.find_all("dd")

        #PER
        #per = float(dd[1].text)
        per = dd[1].text.replace('-','0')
        per = float(per.replace(',', '').strip())
        #12M PER
        per_12m = dd[3].text.replace('-','0')
        per_12m = float(per_12m.replace(',', '').strip())
        #업종PER
        per_ind = dd[5].text.replace('-','0')
        per_ind = float(per_ind.replace(',', '').strip())
        #PBR
        pbr = dd[7].text.replace('-','0')
        pbr = float(pbr.replace(',', '').strip())
        #배당수익률
        div_yid1 = dd[9].text
        div_yid2 = div_yid1.replace('%','')
        div_yid2 = div_yid2.replace('-','0')
        div_yid = float(div_yid2.replace(',', '').strip())

        ### 테이블
        table1 = bs_obj.find("div", {"id":"div1"})
        table2 = table1.find_all("td")

        #거래량
        volume1 = table2[1].text
        volume = int(volume1.replace(',', '').strip())
        #거래대금
        trans_price1 = table2[3].text
        trans_price = int(trans_price1.replace(',', '').strip())
        #시가총액(우선주포함)
        mk_cpt_pfr1 = table2[6].text
        mk_cpt_pfr = int(mk_cpt_pfr1.replace(',', '').strip())
        #시가총액(보통주)
        mk_cpt_cm1 = table2[8].text
        mk_cpt_cm = int(mk_cpt_cm1.replace(',', '').strip())

        # [날짜, 기업정보, 종목코드, 주가, 외국인 보유비중, 상대수익률, per, 12m per, 업종per, pbr, 배당수익률
        #  거래량, 거래 대금, 시가총액(우선주포함), 시가총액(보통주)] 
        res = [[code, corp_name, date, stock_price, fgn_own_ratio, rel_return, per, per_12m, per_ind, pbr, div_yid, volume, trans_price, mk_cpt_pfr, mk_cpt_cm]]
        
        # 재무제표 데이터를 DB에 저장
        mycursor.executemany(query, res)
        con.commit()

    except Exception as e:
        # 오류 발생시 error_list에 티커 저장하고 넘어가기
        print(f"Error for ticker {ticker}: {e}")
        error_list.append(ticker)

    # 무한 크롤링을 방지하기 위해 한 번의 루프가 끝날 때마다 타임슬립을 적용한다.
    time.sleep(0.1)

# DB 연결 종료
engine.dispose()
con.close()
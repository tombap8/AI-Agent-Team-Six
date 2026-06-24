#######################   KOR_FS (참조 : KOR_TICKER)   ####################
## 재무제표 크롤링
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
    insert into kor_fs (계정, 기준일, 값, 종목코드, 공시구분)
    values (%s,%s,%s,%s,%s) as new
    on duplicate key update
    값=new.값
"""

# 오류 발생시 저장할 리스트 생성
error_list = []


# 재무제표 클렌징 함수
## 입력값으로는 데이터프레임, 티커, 공시구분(연간/분기)가 필요하다.
## 먼저 연도의 데이터가 NaN인 항목은 제외한다.
## 열 이름이 ‘계정’, 그리고 재무제표의 월이 결산월과 같은 부분만 선택한다. 
## 계정명이 중복되는 경우 drop_duplicates() 함수를 이용해 첫번째에 위치하는 데이터만 남긴다.
## melt() 함수를 이용해 열로 긴 데이터를 행으로 긴 데이터로 변경한다.
## 계정값이 없는 항목은 제외한다.
## [계산에 참여한 계정 펼치기]라는 글자는 페이지의 [+]에 해당하는 부분이므로 replace() 메서드를 통해 제거한다.
## to_datetime() 메서드를 통해 기준일을 ‘yyyy-mm’ 형태로 바꾼 후, MonthEnd()를 통해 월말에 해당하는 일을 붙인다.
## ‘종목코드’ 열에는 티커를 입력한다.
## ‘공시구분’ 열에는 연간 혹은 분기에 해당하는 값을 입력한다.
def clean_fs(df, ticker, frequency):

    df = df[~df.loc[:, ~df.columns.isin(['계정'])].isna().all(axis=1)]
    df = df.drop_duplicates(['계정'], keep='first')
    df = pd.melt(df, id_vars='계정', var_name='기준일', value_name='값')
    df = df[~pd.isnull(df['값'])]
    df['계정'] = df['계정'].replace({'계산에 참여한 계정 펼치기': ''}, regex=True)
    df['기준일'] = pd.to_datetime(df['기준일'],
                               format='%Y/%m') + pd.tseries.offsets.MonthEnd()
    df['종목코드'] = ticker
    df['공시구분'] = frequency

    return df


# for loop
for i in tqdm(range(0, len(ticker_list))):

    # 티커 선택
    ticker = ticker_list['종목코드'][i]

    # 오류 발생 시 이를 무시하고 다음 루프로 진행
    try:

        # url 생성
        url = f'http://comp.fnguide.com/SVO2/ASP/SVD_Finance.asp?pGB=1&gicode=A{ticker}'

        # 데이터 받아오기
        data = pd.read_html(url, displayed_only=False)

        # 연간 기준 포괄손익계산서(연간)[0], 재무상태표(연간)[2], 현금흐름표(연간)[4] 만 사용함.
        #          포괄손익계산서(분기)[01, 재무상태표(분기)[3], 현금흐름표(분기)[5]
        # 포괄손익계산서 테이블에는 ‘전년동기’, ‘전년동기(%)’ 열이 있으며, 이는 필요하지 않은 내용이므로 삭제
        # concat() 함수를 이용해 포괄손익계산서, 재무상태표, 현금흐름표 세개 테이블을 하나로 묶는다.
        data_fs_y = pd.concat([
            data[0].iloc[:, ~data[0].columns.str.contains('전년동기')], data[2],
            data[4]
        ])
        # rename() 메서드를 통해 첫번째 열 이름(IFRS 혹은 IFRS(연결)을 ‘계정’으로 변경
        data_fs_y = data_fs_y.rename(columns={data_fs_y.columns[0]: "계정"})

        # 결산년 찾기
        # get() 함수를 통해 페이지의 데이터를 불러온다.
        page_data = rq.get(url)
        # content 부분을 BeautifulSoup 객체로 만든다
        page_data_html = BeautifulSoup(page_data.content, 'html.parser')

        # 결산월 항목 [corp_group1 클래스의 div 태그 하부의 h2 태그]에 존재, 
        # select() 함수를 이용해 추출
        fiscal_data = page_data_html.select('div.corp_group1 > h2')
        # fiscal_data 중 첫번째는 종목코드에 해당하고, 
        # 두번째가 결산 데이터에 해당하므로 해당 부분을 선택해 텍스트만 추출
        fiscal_data_text = fiscal_data[1].text
        # ‘n월 결산’ 형태로 텍스트가 구성되어 있으므로, 정규 표현식을 이용해 숫자에 해당하는 부분만 추출
        fiscal_data_text = re.findall('[0-9]+', fiscal_data_text)

        # 결산년에 해당하는 계정만 남기기
        # 결산월에 해당하는 부분만이 선택된다. 이를 이용해 연간 재무제표에 해당하는 열만 선택
        data_fs_y = data_fs_y.loc[:, (data_fs_y.columns == '계정') | (
            data_fs_y.columns.str[-2:].isin(fiscal_data_text))]

        # 클렌징
        data_fs_y_clean = clean_fs(data_fs_y, ticker, 'y')

        # 분기 데이터
        data_fs_q = pd.concat([
            data[1].iloc[:, ~data[1].columns.str.contains('전년동기')], data[3],
            data[5]
        ])
        data_fs_q = data_fs_q.rename(columns={data_fs_q.columns[0]: "계정"})

        data_fs_q_clean = clean_fs(data_fs_q, ticker, 'q')

        # 두개 합치기
        data_fs_bind = pd.concat([data_fs_y_clean, data_fs_q_clean])

        # 재무제표 데이터를 DB에 저장
        args = data_fs_bind.values.tolist()
        mycursor.executemany(query, args)
        con.commit()

    except:

        # 오류 발생시 해당 종목명을 저장하고 다음 루프로 이동
        print(ticker)
        error_list.append(ticker)

    # 타임슬립 적용
    time.sleep(0.1)

# DB 연결 종료
engine.dispose()
con.close()

#################   KOR_VALUE (참조 : KOR_TICKER / KOR_FS)   ###############
# 전 종목 가치지표 계산
# 패키지 불러오기
import pymysql
from sqlalchemy import create_engine
import pandas as pd
import numpy as np

# DB 연결
from utils.db_helper import get_engine, get_connection

engine = get_engine()
con = get_connection()
mycursor = con.cursor()

# 분기 재무제표 불러오기
kor_fs = pd.read_sql("""
select * from kor_fs
where 공시구분 = 'q'
and 계정 in ('당기순이익', '자본', '영업활동으로인한현금흐름', '매출액');
""", con=engine)

# 티커 리스트 불러오기
ticker_list = pd.read_sql("""
select * from kor_ticker
where 기준일 = (select max(기준일) from kor_ticker) 
  and 종목구분 = '보통주';
""", con=engine)

engine.dispose()

# TTM 구하기
kor_fs = kor_fs.sort_values(['종목코드', '계정', '기준일'])
 #종목코드와 계정을 기준으로 groupby() 함수를 통해 그룹을 묶으며, 
 #as_index=False를 통해 그룹 라벨을 인덱스로 사용하지 않는다.
 #rolling() 메서드를 통해 4개 기간씩 합계를 구하며, 
 #min_periods 인자를 통해 데이터가 최소 4개는 있을 경우에만 값을 구한다. 
 #즉 4개 분기 데이터를 통해 TTM 값을 계산하며, 12개월치 데이터가 없을 경우는 계산을 하지 않는다.
kor_fs['ttm'] = kor_fs.groupby(['종목코드', '계정'], as_index=False)['값'].rolling(
    window=4, min_periods=4).sum()['값']

# 자본은 평균 구하기
#‘자본’ 항목은 재무상태표에 해당하는 항목이므로 합이 아닌 4로 나누어 평균을 구하며, 
#타 헝목은 4분기 기준 합을 그대로 사용한다.
kor_fs['ttm'] = np.where(kor_fs['계정'] == '자본', kor_fs['ttm'] / 4,
                         kor_fs['ttm'])
kor_fs = kor_fs.groupby(['계정', '종목코드']).tail(1)

# 티커리스트의 시가총액 데이터를 이용해 가치지표를 계산
# TTM 기준으로 계산된 재무제표 테이블과 티커리스트 테이블을 합친다.
kor_fs_merge = kor_fs[['계정', '종목코드',
                       'ttm']].merge(ticker_list[['종목코드', '시가총액', '기준일']],
                                     on='종목코드')
# 시가총액을 단위를 억원.                                     
kor_fs_merge['시가총액'] = kor_fs_merge['시가총액'] / 100000000

#시가총액을 재무데이터 값으로 나누어 가치지표를 계산한 후, 반올림을 한다.
kor_fs_merge['value'] = kor_fs_merge['시가총액'] / kor_fs_merge['ttm']
kor_fs_merge['value'] = kor_fs_merge['value'].round(4)
# 각 계정에 맞게 계정명(PSR, PCR, PER, PBR)을 적는다.
kor_fs_merge['지표'] = np.where(
    kor_fs_merge['계정'] == '매출액', 'PSR',
    np.where(
        kor_fs_merge['계정'] == '영업활동으로인한현금흐름', 'PCR',
        np.where(kor_fs_merge['계정'] == '자본', 'PBR',
                 np.where(kor_fs_merge['계정'] == '당기순이익', 'PER', None))))

# rename() 메서드를 통해 ‘value’라는 열 이름을 ‘값’으로 변경한다.
kor_fs_merge.rename(columns={'value': '값'}, inplace=True)
# 필요한 열만 선택한 후, replace() 메서드를 통해 inf와 nan를 None으로 변경한다.
kor_fs_merge = kor_fs_merge[['종목코드', '기준일', '지표', '값']]
kor_fs_merge = kor_fs_merge.replace([np.inf, -np.inf, np.nan], None)

kor_fs_merge.head(4)

# 계산가치된 지표를 데이터베이스에 저장
query = """
    insert into kor_value (종목코드, 기준일, 지표, 값)
    values (%s,%s,%s,%s) as new
    on duplicate key update
    값=new.값
"""

args_fs = kor_fs_merge.values.tolist()
mycursor.executemany(query, args_fs)
con.commit()

# 배당수익률의 경우 티커리스트를 통해 한번에 계산
ticker_list['값'] = ticker_list['주당배당금'] / ticker_list['종가']
ticker_list['값'] = ticker_list['값'].round(4)
ticker_list['지표'] = 'DY'
dy_list = ticker_list[['종목코드', '기준일', '지표', '값']]
dy_list = dy_list.replace([np.inf, -np.inf, np.nan], None)
dy_list = dy_list[dy_list['값'] != 0]

dy_list.head()

# 배당수익률 역시 kor_value 테이블에 upsert 방식으로 저장
args_dy = dy_list.values.tolist()
mycursor.executemany(query, args_dy)
con.commit()

engine.dispose()
con.close()

#Type : list => Dataframe 으로 변환후 엑셀로 저장해야함...
# DataFrame 생성
#error_df = pd.DataFrame(error_list)
# 엑셀 파일 저장 (error_list 내용을 확인해 보자!!!)
#error_df.to_excel('error_list.xlsx', index=False)

#kor_ticker의 종목구분='보통주' 인 경우 에러가 발생하지 않음...
#from sqlalchemy import create_engine
##SQL에는 NaN이 입력되지 않으므로, None으로 변경한다.
#engine = create_engine('mysql+pymysql://root:jhsong89@127.0.0.1:3306/stock_db')
#error_df = error_df.replace({np.nan: None})
#error_df.to_sql(name='error_list', con=engine, index=False, if_exists='replace')
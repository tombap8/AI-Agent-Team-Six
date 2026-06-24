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

# 최근년도 공시 재무제표 불러오기
kor_fs = pd.read_sql("""
select 종목코드, 계정, 공시구분, 기준일, 값 
	from
	(
		select * , row_number() over (partition by 종목코드, 계정, 공시구분  order by 기준일 desc) 순위 
		from kor_fs 
		where 1 = 1
		  and 공시구분 = 'y'
		  and 계정 in ('당기순이익', '자본', '영업활동으로인한현금흐름', '매출액')
	) as a
where a.순위 = 1 ;
""", con=engine)

# 티커 리스트 불러오기
ticker_list = pd.read_sql("""
select * from kor_ticker
where 기준일 = (select max(기준일) from kor_ticker) 
  and 종목구분 = '보통주';
""", con=engine)

engine.dispose()


kor_fs.rename(columns={'값': 'ttm'}, inplace=True)

# 티커리스트의 시가총액 데이터를 이용해 가치지표를 계산
kor_fs_merge = kor_fs[['계정', '종목코드',
                       'ttm']].merge(ticker_list[['종목코드', '시가총액', '기준일']],
                                     on='종목코드')
kor_fs_merge['시가총액'] = kor_fs_merge['시가총액'] / 100000000

kor_fs_merge['value'] = kor_fs_merge['시가총액'] / kor_fs_merge['ttm']
kor_fs_merge['value'] = kor_fs_merge['value'].round(4)
kor_fs_merge['지표'] = np.where(
    kor_fs_merge['계정'] == '매출액', 'PSR',
    np.where(
        kor_fs_merge['계정'] == '영업활동으로인한현금흐름', 'PCR',
        np.where(kor_fs_merge['계정'] == '자본', 'PBR',
                 np.where(kor_fs_merge['계정'] == '당기순이익', 'PER', None))))

kor_fs_merge.rename(columns={'value': '값'}, inplace=True)
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
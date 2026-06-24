import sys
sys.path.append("c:\\AI-Agent\\quant_py")
from utils.db_helper import get_connection

try:
    con = get_connection()
    cursor = con.cursor()
    
    ddl = """
    CREATE TABLE IF NOT EXISTS kor_fs_value (
        종목코드 varchar(6) not null,
        종목명 varchar(20),
        기준일 date not null,
        주가 double,
        외국인보유비중 double,
        상대수익률 double,
        PER double,
        PER_12M double,
        업종PER double,
        PBR double,
        DY double,
        거래량 double,
        거래대금 double,
        시가총액 double,
        시가총액_보통주 double,
        PRIMARY KEY (종목코드, 기준일)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """
    
    cursor.execute(ddl)
    con.commit()
    con.close()
    print("Table 'kor_fs_value' created or already exists.")
except Exception as e:
    print("Error:", e)

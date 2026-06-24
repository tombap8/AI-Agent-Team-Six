import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import datetime
import random
import re
import numpy as np
import pandas as pd
from scipy.stats import zscore
from utils.db_helper import get_engine, get_connection

def recreate_table_using_ddl(cursor, table_name):
    # Search in parent directory for 테이블생성.sql
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    sql_path = os.path.join(parent_dir, "테이블생성.sql")
    
    if not os.path.exists(sql_path):
        raise FileNotFoundError(f"테이블생성.sql not found at {sql_path}")
        
    with open(sql_path, "r", encoding="utf-8") as f:
        content = f.read()
        
    # Remove single line comments
    content_clean = re.sub(r'--.*$', '', content, flags=re.MULTILINE)
    
    # Split by semicolon
    statements = content_clean.split(";")
    
    ddl_statement = None
    for stmt in statements:
        stmt_strip = stmt.strip()
        pattern = r"CREATE\s+TABLE\s+`?" + re.escape(table_name) + r"`?\s*\("
        if re.search(pattern, stmt_strip, re.IGNORECASE):
            ddl_statement = stmt_strip + ";"
            break
            
    if not ddl_statement:
        raise ValueError(f"Could not find DDL for table: {table_name} in 테이블생성.sql")
        
    # Execute drop table
    cursor.execute(f"DROP TABLE IF EXISTS `{table_name}`;")
    # Execute create table
    cursor.execute(ddl_statement)


# 30 major KOSPI stocks list
KOR_STOCKS = [
    {"code": "005930", "name": "삼성전자", "sector": "IT", "price": 75000, "mcap": 447000000000000},
    {"code": "000660", "name": "SK하이닉스", "sector": "IT", "price": 180000, "mcap": 131000000000000},
    {"code": "035420", "name": "NAVER", "sector": "커뮤니케이션서비스", "price": 170000, "mcap": 27000000000000},
    {"code": "035720", "name": "카카오", "sector": "커뮤니케이션서비스", "price": 45000, "mcap": 20000000000000},
    {"code": "005380", "name": "현대차", "sector": "경기관련소비재", "price": 250000, "mcap": 52000000000000},
    {"code": "000270", "name": "기아", "sector": "경기관련소비재", "price": 110000, "mcap": 44000000000000},
    {"code": "051910", "name": "LG화학", "sector": "소재", "price": 360000, "mcap": 25000000000000},
    {"code": "005490", "name": "POSCO홀딩스", "sector": "소재", "price": 370000, "mcap": 31000000000000},
    {"code": "006400", "name": "삼성SDI", "sector": "소재", "price": 380000, "mcap": 26000000000000},
    {"code": "068270", "name": "셀트리온", "sector": "건강관리", "price": 190000, "mcap": 41000000000000},
    {"code": "207940", "name": "삼성바이오로직스", "sector": "건강관리", "price": 740000, "mcap": 52000000000000},
    {"code": "055550", "name": "신한지주", "sector": "금융", "price": 48000, "mcap": 24000000000000},
    {"code": "105560", "name": "KB금융", "sector": "금융", "price": 78000, "mcap": 31000000000000},
    {"code": "086790", "name": "하나금융지주", "sector": "금융", "price": 62000, "mcap": 18000000000000},
    {"code": "316140", "name": "우리금융지주", "sector": "금융", "price": 14000, "mcap": 10000000000000},
    {"code": "015760", "name": "한국전력", "sector": "유틸리티", "price": 21000, "mcap": 13000000000000},
    {"code": "036460", "name": "한국가스공사", "sector": "유틸리티", "price": 42000, "mcap": 3800000000000},
    {"code": "011200", "name": "HMM", "sector": "산업재", "price": 18000, "mcap": 12000000000000},
    {"code": "003490", "name": "대한항공", "sector": "산업재", "price": 22000, "mcap": 8000000000000},
    {"code": "086280", "name": "현대글로비스", "sector": "산업재", "price": 120000, "mcap": 9000000000000},
    {"code": "010950", "name": "S-Oil", "sector": "에너지", "price": 68000, "mcap": 7600000000000},
    {"code": "096770", "name": "SK이노베이션", "sector": "에너지", "price": 105000, "mcap": 10000000000000},
    {"code": "000100", "name": "유한양행", "sector": "건강관리", "price": 75000, "mcap": 6000000000000},
    {"code": "090430", "name": "아모레퍼시픽", "sector": "경기관련소비재", "price": 140000, "mcap": 8200000000000},
    {"code": "139480", "name": "이마트", "sector": "경기관련소비재", "price": 60000, "mcap": 1600000000000},
    {"code": "271560", "name": "오리온", "sector": "필수소비재", "price": 95000, "mcap": 3700000000000},
    {"code": "097950", "name": "CJ제일제당", "sector": "필수소비재", "price": 320000, "mcap": 5000000000000},
    {"code": "033780", "name": "KT&G", "sector": "필수소비재", "price": 92000, "mcap": 11000000000000},
    {"code": "066570", "name": "LG전자", "sector": "IT", "price": 100000, "mcap": 16000000000000},
    {"code": "028260", "name": "삼성물산", "sector": "산업재", "price": 145000, "mcap": 27000000000000}
]

# 10 major US tech/blue-chip stocks
US_STOCKS = [
    {"code": "AAPL", "name": "Apple Inc.", "sector": "IT", "price": 180, "mcap": 2800000000000},
    {"code": "MSFT", "name": "Microsoft Corp.", "sector": "IT", "price": 420, "mcap": 3100000000000},
    {"code": "GOOGL", "name": "Alphabet Inc.", "sector": "커뮤니케이션서비스", "price": 170, "mcap": 2100000000000},
    {"code": "AMZN", "name": "Amazon.com Inc.", "sector": "경기관련소비재", "price": 180, "mcap": 1900000000000},
    {"code": "NVDA", "name": "NVIDIA Corp.", "sector": "IT", "price": 900, "mcap": 2200000000000},
    {"code": "META", "name": "Meta Platforms Inc.", "sector": "커뮤니케이션서비스", "price": 480, "mcap": 1200000000000},
    {"code": "TSLA", "name": "Tesla Inc.", "sector": "경기관련소비재", "price": 170, "mcap": 550000000000},
    {"code": "JPM", "name": "JPMorgan Chase & Co.", "sector": "금융", "price": 190, "mcap": 560000000000},
    {"code": "UNH", "name": "UnitedHealth Group", "sector": "건강관리", "price": 490, "mcap": 450000000000},
    {"code": "XOM", "name": "Exxon Mobil Corp.", "sector": "에너지", "price": 115, "mcap": 460000000000}
]

def generate_market_data(stocks_list, prefix="kor"):
    engine = get_engine()
    con = get_connection()
    cursor = con.cursor()
    
    # Fetch recent tickers from the database if they exist before dropping tables
    recent_stocks = []
    try:
        query = f"""
            SELECT t.종목코드 as code, t.종목명 as name, s.SEC_NM_KOR as sector, t.종가 as price, t.시가총액 as mcap
            FROM `{prefix}_ticker` t
            LEFT JOIN `{prefix}_sector` s ON t.종목코드 = s.CMP_CD AND t.기준일 = s.기준일
            WHERE t.기준일 = (SELECT MAX(기준일) FROM `{prefix}_ticker`)
        """
        df_existing = pd.read_sql(query, con=engine)
        if not df_existing.empty:
            df_existing = df_existing.dropna(subset=['code', 'name', 'price', 'mcap'])
            df_existing['sector'] = df_existing['sector'].fillna('기타')
            recent_stocks = df_existing.to_dict(orient='records')
            print(f"Loaded {len(recent_stocks)} recent tickers from {prefix}_ticker.")
    except Exception as e:
        print(f"Could not load recent tickers from database: {e}. Falling back to default list.")
        
    if recent_stocks:
        stocks_list = recent_stocks
        
    # Drop and recreate tables using DDL from 테이블생성.sql for correct schemas
    tables = [f'{prefix}_multi_factor', f'{prefix}_ticker', f'{prefix}_sector', f'{prefix}_price', f'{prefix}_fs', f'{prefix}_value']
    for t in tables:
        try:
            recreate_table_using_ddl(cursor, t)
        except Exception as e:
            print(f"Error recreating {t} using DDL: {e}")
            try:
                cursor.execute(f"DROP TABLE IF EXISTS `{t}`;")
            except Exception:
                pass
    con.commit()
    
    today = datetime.date.today()
    
    # 1. Generate ticker and sector
    ticker_rows = []
    sector_rows = []
    
    for s in stocks_list:
        eps = round(s["price"] / random.uniform(8.0, 20.0), 2)
        bps = round(s["price"] / random.uniform(0.4, 1.8), 2)
        dps = round(s["price"] * random.uniform(0.01, 0.05), 2)
        dy = round((dps / s["price"]) * 100, 4)
        
        ticker_rows.append({
            "종목코드": s["code"],
            "종목명": s["name"],
            "시장구분": "KOSPI" if prefix == "kor" else "US",
            "종가": s["price"],
            "시가총액": s["mcap"],
            "기준일": today,
            "EPS": eps,
            "BPS": bps,
            "주당배당금": dps,
            "종목구분": "보통주"
        })
        
        sector_rows.append({
            "IDX_CD": "G" + str(random.randint(10, 55)),
            "CMP_CD": s["code"],
            "CMP_KOR": s["name"],
            "SEC_NM_KOR": s["sector"],
            "기준일": today
        })

    df_ticker = pd.DataFrame(ticker_rows)
    df_sector = pd.DataFrame(sector_rows)
    
    df_ticker.to_sql(f'{prefix}_ticker', con=engine, index=False, if_exists='append', chunksize=10000)
    df_sector.to_sql(f'{prefix}_sector', con=engine, index=False, if_exists='append', chunksize=10000)
        
    # 2. Generate daily price (250 trading days)
    price_rows = []
    
    for s in stocks_list:
        base_price = s["price"]
        current_price = base_price
        for day_idx in range(250):
            date_val = today - datetime.timedelta(days=day_idx * 1.45)
            daily_ret = random.normalvariate(0.0002, 0.015)
            close_p = round(current_price, 2) if prefix == "global" else round(current_price)
            open_p = round(close_p * (1 - daily_ret * 0.2), 2) if prefix == "global" else round(close_p * (1 - daily_ret * 0.2))
            high_p = round(max(open_p, close_p) * (1 + abs(daily_ret) * 0.1), 2) if prefix == "global" else round(max(open_p, close_p) * (1 + abs(daily_ret) * 0.1))
            low_p = round(min(open_p, close_p) * (1 - abs(daily_ret) * 0.1), 2) if prefix == "global" else round(min(open_p, close_p) * (1 - abs(daily_ret) * 0.1))
            vol = int(random.uniform(50000, 1500000))
            
            price_rows.append({
                "날짜": date_val,
                "시가": open_p,
                "고가": high_p,
                "저가": low_p,
                "종가": close_p,
                "거래량": vol,
                "종목코드": s["code"]
            })
            current_price = current_price / (1 + daily_ret)
            
    df_price = pd.DataFrame(price_rows)
    df_price.to_sql(f'{prefix}_price', con=engine, index=False, if_exists='append', chunksize=10000)
        
    # 3. Generate fs and value
    fs_rows = []
    value_rows = []
    
    accounts = ['당기순이익', '자본', '영업활동으로인한현금흐름', '매출액', '자산', '매출총이익']
    indicators = ['PER', 'PBR', 'PSR', 'PCR', 'DY']
    
    for s in stocks_list:
        cap = s["mcap"] / 100000000 if prefix == "kor" else s["mcap"] # scale KOR to 100M KRW, US stays raw USD
        
        f_netinc = cap / random.uniform(6.0, 18.0)
        f_equity = cap / random.uniform(0.5, 2.0)
        f_sales = cap / random.uniform(0.2, 1.5)
        f_cfo = f_netinc * random.uniform(0.8, 1.5)
        f_assets = f_equity * random.uniform(1.2, 2.5)
        f_gpa = f_sales * random.uniform(0.2, 0.5)
        
        for date_offset in range(4):
            q_date = today - datetime.timedelta(days=date_offset * 90)
            for acc, val in zip(accounts, [f_netinc, f_equity, f_cfo, f_sales, f_assets, f_gpa]):
                q_val = val / 4.0 * random.uniform(0.9, 1.1)
                fs_rows.append({
                    "계정": acc,
                    "기준일": q_date,
                    "값": q_val,
                    "종목코드": s["code"],
                    "공시구분": "q"
                })
                if date_offset == 0:
                    fs_rows.append({
                        "계정": acc,
                        "기준일": today,
                        "값": val,
                        "종목코드": s["code"],
                        "공시구분": "y"
                    })
                    
        val_mapping = {
            'PER': cap / f_netinc,
            'PBR': cap / f_equity,
            'PSR': cap / f_sales,
            'PCR': cap / f_cfo,
            'DY': random.uniform(1.0, 5.0)
        }
        for ind in indicators:
            value_rows.append({
                "종목코드": s["code"],
                "기준일": today,
                "지표": ind,
                "값": val_mapping[ind]
            })
            
    df_fs = pd.DataFrame(fs_rows)
    df_value = pd.DataFrame(value_rows)
    
    df_fs.to_sql(f'{prefix}_fs', con=engine, index=False, if_exists='append', chunksize=10000)
    df_value.to_sql(f'{prefix}_value', con=engine, index=False, if_exists='append', chunksize=10000)
        
    # 4. Generate multi_factor
    multi_factor_rows = []
    
    for s in stocks_list:
        cap = s["mcap"] / 100000000 if prefix == "kor" else s["mcap"]
        f_netinc = cap / random.uniform(6.0, 18.0)
        f_equity = cap / random.uniform(0.5, 2.0)
        f_sales = cap / random.uniform(0.2, 1.5)
        f_cfo = f_netinc * random.uniform(0.8, 1.5)
        f_assets = f_equity * random.uniform(1.2, 2.5)
        f_gpa = f_sales * random.uniform(0.2, 0.5)
        
        roe = f_netinc / f_equity
        gpa = f_gpa / f_assets
        cfo = f_cfo / f_assets
        dy = random.uniform(0.01, 0.05)
        pbr = cap / f_equity
        pcr = cap / f_cfo
        per = cap / f_netinc
        psr = cap / f_sales
        m12 = random.uniform(-0.15, 0.35)
        k_ratio = random.uniform(-15.0, 35.0)
        
        multi_factor_rows.append({
            "종목코드": s["code"],
            "종목명": s["name"],
            "기준일": today,
            "SEC_NM_KOR": s["sector"],
            "자본": f_equity,
            "자산": f_assets,
            "당기순이익": f_netinc,
            "매출총이익": f_gpa,
            "영업활동으로인한현금흐름": f_cfo,
            "ROE": roe,
            "GPA": gpa,
            "CFO": cfo,
            "DY": dy,
            "PBR": pbr,
            "PCR": pcr,
            "PER": per,
            "PSR": psr,
            "12M": m12,
            "K_ratio": k_ratio
        })
        
    df_mf = pd.DataFrame(multi_factor_rows)
    
    def col_clean_init(series, cutoff=0.01, asc=False):
        q_low = series.quantile(cutoff)
        q_hi = series.quantile(1 - cutoff)
        trimmed = series.copy()
        trimmed[series < q_low] = q_low
        trimmed[series > q_hi] = q_hi
        
        ranked = trimmed.rank(ascending=asc)
        if len(ranked.unique()) <= 1:
            return pd.Series(0.0, index=series.index)
        return zscore(ranked)

    df_mf['z_quality'] = col_clean_init(df_mf['ROE'], 0.01, False) + col_clean_init(df_mf['GPA'], 0.01, False) + col_clean_init(df_mf['CFO'], 0.01, False)
    df_mf['z_value'] = (col_clean_init(df_mf['PER'], 0.01, True) + 
                        col_clean_init(df_mf['PBR'], 0.01, True) + 
                        col_clean_init(df_mf['PSR'], 0.01, True) + 
                        col_clean_init(df_mf['PCR'], 0.01, True) + 
                        col_clean_init(df_mf['DY'], 0.01, False))
    df_mf['z_momentum'] = col_clean_init(df_mf['12M'], 0.01, False) + col_clean_init(df_mf['K_ratio'], 0.01, False)
    
    df_mf['qvm'] = (df_mf['z_quality'] + df_mf['z_value'] + df_mf['z_momentum'])
    df_mf['invest'] = np.where(df_mf['qvm'].rank(ascending=False) <= 20, 'Y', 'N')
    
    df_mf.to_sql(f'{prefix}_multi_factor', con=engine, index=False, if_exists='append', chunksize=10000)
    try:
        cursor.execute(f"ALTER TABLE `{prefix}_multi_factor` MODIFY `종목코드` VARCHAR(6) NOT NULL;")
        cursor.execute(f"ALTER TABLE `{prefix}_multi_factor` MODIFY `기준일` DATE NOT NULL;")
        cursor.execute(f"ALTER TABLE `{prefix}_multi_factor` ADD PRIMARY KEY (`종목코드`, `기준일`);")
    except Exception as e:
        print(f"Could not add primary key for multi_factor: {e}")
        
    con.commit()
    engine.dispose()
    con.close()
    print(f"Successfully generated {prefix} tables in stock_db!")

def generate_sample_data():
    generate_market_data(KOR_STOCKS, prefix="kor")
    generate_market_data(US_STOCKS, prefix="global")
    print("All mock databases (KOR & US) created and populated successfully!")

if __name__ == '__main__':
    generate_sample_data()

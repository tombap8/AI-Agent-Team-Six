import sys
import os
sys.path.append("c:\\AI-Agent\\quant_py")

from utils.db_helper import get_connection

try:
    con = get_connection()
    cursor = con.cursor()
    
    # Check tables
    tables = ['kor_ticker', 'kor_sector', 'kor_price', 'kor_fs', 'kor_value']
    for table in tables:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"Table '{table}': {count} records")
        except Exception as e:
            print(f"Table '{table}' Error: {e}")
            
    con.close()
except Exception as e:
    print("Database connection error:", e)

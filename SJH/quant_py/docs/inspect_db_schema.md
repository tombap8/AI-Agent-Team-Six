import sys
sys.path.append("c:\\AI-Agent\\quant_py")
from utils.db_helper import get_connection

try:
    con = get_connection()
    cursor = con.cursor()
    cursor.execute("DESCRIBE kor_ticker")
    columns = cursor.fetchall()
    print("--- kor_ticker columns ---")
    for col in columns:
        print(col)
    con.close()
except Exception as e:
    print("Error:", e)

import sys
sys.path.append("c:\\AI-Agent\\quant_py")
from utils.db_helper import get_connection

try:
    con = get_connection()
    cursor = con.cursor()
    cursor.execute("SHOW TABLES")
    tables = cursor.fetchall()
    print("--- DB Tables ---")
    for t in tables:
        print(t[0])
    con.close()
except Exception as e:
    print("Error:", e)

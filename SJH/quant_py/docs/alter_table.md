import sys
sys.path.append("c:\\AI-Agent\\quant_py")
from utils.db_helper import get_connection

try:
    con = get_connection()
    cursor = con.cursor()
    
    # Add columns if they do not exist
    alter_queries = [
        "ALTER TABLE kor_ticker ADD COLUMN PER float DEFAULT NULL",
        "ALTER TABLE kor_ticker ADD COLUMN PBR float DEFAULT NULL",
        "ALTER TABLE kor_ticker ADD COLUMN 배당수익률 float DEFAULT NULL"
    ]
    
    for query in alter_queries:
        try:
            cursor.execute(query)
            print("Executed:", query)
        except Exception as e:
            print("Failed to execute:", query, "-", e)
            
    con.commit()
    con.close()
    print("Table alteration finished.")
except Exception as e:
    print("Error:", e)

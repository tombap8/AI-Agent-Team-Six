import os
import re

def get_ddl_for_table(table_name):
    # Search in parent directory for 테이블생성.sql
    sql_path = r"c:\AI-Agent\quant_py\테이블생성.sql"
    if not os.path.exists(sql_path):
        return None
        
    with open(sql_path, "r", encoding="utf-8") as f:
        content = f.read()
        
    # Remove single line comments
    content_clean = re.sub(r'--.*$', '', content, flags=re.MULTILINE)
    
    # Split by semicolon
    statements = content_clean.split(";")
    
    for stmt in statements:
        stmt_strip = stmt.strip()
        # Find if this statement is the CREATE TABLE for our table
        # Matches CREATE TABLE `table_name` or CREATE TABLE table_name (case-insensitive, ignoring backticks)
        pattern = r"CREATE\s+TABLE\s+`?" + re.escape(table_name) + r"`?\s*\("
        if re.search(pattern, stmt_strip, re.IGNORECASE):
            return stmt_strip + ";"
            
    return None

if __name__ == '__main__':
    tables = ['kor_ticker', 'global_ticker', 'kor_price', 'global_price', 'kor_fs', 'global_fs', 'kor_value', 'global_value', 'kor_multi_factor', 'global_multi_factor']
    for t in tables:
        ddl = get_ddl_for_table(t)
        if ddl:
            print(f"--- DDL FOR {t} ---")
            print(ddl[:200] + "...")
        else:
            print(f"FAILED TO FIND DDL FOR {t}")

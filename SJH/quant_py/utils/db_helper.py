import os
import pymysql
from sqlalchemy import create_engine
from dotenv import load_dotenv

# .env 파일 위치 로드 (utils 폴더의 상위 폴더인 프로젝트 루트 기준)
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
load_dotenv(os.path.join(parent_dir, '.env'))

DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "1234")
DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_NAME = os.getenv("DB_NAME", "stock_db")

def get_engine():
    """SQLAlchemy 엔진 객체를 반환합니다."""
    db_url = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    return create_engine(db_url)

def get_connection():
    """PyMySQL 커넥션 객체를 반환합니다."""
    return pymysql.connect(
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=int(DB_PORT),
        database=DB_NAME,
        charset='utf8'
    )

import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "database.db")

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    # 1. Users Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Users (
        user_uuid TEXT PRIMARY KEY,
        auth_phone TEXT UNIQUE NOT NULL,
        user_role TEXT NOT NULL CHECK(user_role IN ('SELLER', 'BUYER', 'HQ_ADMIN')),
        registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    
    # 2. StoreProperties Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS StoreProperties (
        store_uuid TEXT PRIMARY KEY,
        owner_uuid TEXT,
        biz_reg_no TEXT UNIQUE NOT NULL,
        store_brand TEXT NOT NULL,
        established_date TEXT NOT NULL,
        address_detail TEXT NOT NULL,
        verification_status TEXT DEFAULT 'PENDING' CHECK(verification_status IN ('PENDING', 'REAL_VALID', 'BLOCKED_FAKE')),
        FOREIGN KEY(owner_uuid) REFERENCES Users(user_uuid)
    );
    """)
    
    # 3. Valuations Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Valuations (
        valuation_id INTEGER PRIMARY KEY AUTOINCREMENT,
        store_uuid TEXT,
        val_facility REAL NOT NULL DEFAULT 0.0,
        val_operating REAL NOT NULL DEFAULT 0.0,
        val_location REAL NOT NULL DEFAULT 0.0,
        val_license REAL NOT NULL DEFAULT 0.0,
        calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(store_uuid) REFERENCES StoreProperties(store_uuid)
    );
    """)
    
    conn.commit()
    conn.close()

def seed_mock_data():
    conn = get_connection()
    cursor = conn.cursor()
    
    # Check if we already have data
    cursor.execute("SELECT COUNT(*) FROM Users")
    if cursor.fetchone()[0] > 0:
        conn.close()
        return
    
    mock_users = [
        ("user-seller-01", "010-1234-5678", "SELLER"),
        ("user-seller-02", "010-9876-5432", "SELLER"),
        ("user-seller-03", "010-5555-4444", "SELLER"),
        ("user-buyer-01", "010-1111-2222", "BUYER"),
        ("user-hq-01", "010-3333-7777", "HQ_ADMIN")
    ]
    
    mock_stores = [
        ("store-cafe-01", "user-seller-01", "120-81-12345", "메가커피 대치점 (Mega Coffee)", "2022-03-15", "서울특별시 강남구 대치동 988-1", "REAL_VALID"),
        ("store-chicken-01", "user-seller-02", "204-12-67890", "교촌치킨 홍대입구점 (Kyochon)", "2021-07-20", "서울특별시 마포구 서교동 365-8", "REAL_VALID"),
        ("store-mart-01", "user-seller-03", "110-45-99999", "이마트24 역삼역점 (Emart24)", "2023-01-10", "서울특별시 강남구 역삼동 736-1", "REAL_VALID"),
        ("store-fake-01", "user-seller-01", "999-99-99999", "가짜 스타벅스 청담점", "2025-12-25", "서울특별시 강남구 청담동 123", "BLOCKED_FAKE")
    ]
    
    mock_valuations = [
        ("store-cafe-01", 35000000.0, 48000000.0, 20000000.0, 5000000.0),
        ("store-chicken-01", 25000000.0, 36000000.0, 15000000.0, 2000000.0),
        ("store-mart-01", 42000000.0, 54000000.0, 30000000.0, 8000000.0),
        ("store-fake-01", 0.0, 0.0, 0.0, 0.0)
    ]
    
    for u in mock_users:
        cursor.execute("INSERT INTO Users (user_uuid, auth_phone, user_role) VALUES (?, ?, ?)", u)
        
    for s in mock_stores:
        cursor.execute("INSERT INTO StoreProperties (store_uuid, owner_uuid, biz_reg_no, store_brand, established_date, address_detail, verification_status) VALUES (?, ?, ?, ?, ?, ?, ?)", s)
        
    for v in mock_valuations:
        cursor.execute("INSERT INTO Valuations (store_uuid, val_facility, val_operating, val_location, val_license) VALUES (?, ?, ?, ?, ?)", v)
        
    conn.commit()
    conn.close()

def get_store_listings():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT s.*, v.val_facility, v.val_operating, v.val_location, v.val_license,
               (v.val_facility + v.val_operating + v.val_location + v.val_license) as total_valuation,
               u.auth_phone
        FROM StoreProperties s
        LEFT JOIN Valuations v ON s.store_uuid = v.store_uuid
        LEFT JOIN Users u ON s.owner_uuid = u.user_uuid
        WHERE s.verification_status != 'BLOCKED_FAKE'
    """)
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_store_by_id(store_uuid):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT s.*, v.val_facility, v.val_operating, v.val_location, v.val_license,
               (v.val_facility + v.val_operating + v.val_location + v.val_license) as total_valuation,
               u.auth_phone
        FROM StoreProperties s
        LEFT JOIN Valuations v ON s.store_uuid = v.store_uuid
        LEFT JOIN Users u ON s.owner_uuid = u.user_uuid
        WHERE s.store_uuid = ?
    """, (store_uuid,))
    row = cursor.fetchone()
    conn.close()
    return row

def register_store(store_uuid, owner_phone, biz_reg_no, store_brand, established_date, address_detail, val_facility=0, val_operating=0, val_location=0, val_license=0, status='PENDING'):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        # Check if user exists, if not create
        cursor.execute("SELECT user_uuid FROM Users WHERE auth_phone = ?", (owner_phone,))
        user_row = cursor.fetchone()
        if user_row:
            owner_uuid = user_row["user_uuid"]
        else:
            owner_uuid = f"user-{os.urandom(4).hex()}"
            cursor.execute("INSERT INTO Users (user_uuid, auth_phone, user_role) VALUES (?, ?, 'SELLER')", (owner_uuid, owner_phone))
            
        cursor.execute("""
            INSERT INTO StoreProperties (store_uuid, owner_uuid, biz_reg_no, store_brand, established_date, address_detail, verification_status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (store_uuid, owner_uuid, biz_reg_no, store_brand, established_date, address_detail, status))
        
        cursor.execute("""
            INSERT INTO Valuations (store_uuid, val_facility, val_operating, val_location, val_license)
            VALUES (?, ?, ?, ?, ?)
        """, (store_uuid, val_facility, val_operating, val_location, val_license))
        
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"DB Error: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

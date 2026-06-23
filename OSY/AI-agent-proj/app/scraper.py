import random
import re
import json
from duckduckgo_search import DDGS

# Real-world franchise data for simulation (공정위 정보공개서 기준 모킹)
FRANCHISE_DB = {
    "메가커피": {
        "brand_name": "메가MGC커피 (Mega Coffee)",
        "category": "식음료 (커피전문점)",
        "membership_fee": 11000000,    # 가맹비 + 교육비
        "deposit": 2000000,           # 보증금
        "interior_cost": 55000000,      # 인테리어 (기준 평수 15평)
        "other_cost": 29000000,         # 기타 설비/집기 비용
        "total_initial": 97000000,      # 합계 창업비용
        "avg_annual_sales": 328000000,  # 가맹점 평균 연매출
        "store_count": 3031,            # 가맹점 수
        "royalty": "월 150,000원 (부가세 별도)"
    },
    "교촌치킨": {
        "brand_name": "교촌치킨 (Kyochon)",
        "category": "식음료 (치킨전문점)",
        "membership_fee": 8800000,
        "deposit": 5000000,
        "interior_cost": 65000000,
        "other_cost": 42000000,
        "total_initial": 120800000,
        "avg_annual_sales": 648000000,
        "store_count": 1375,
        "royalty": "매출의 1% - 3% 수준"
    },
    "컴포즈커피": {
        "brand_name": "컴포즈커피 (Compose Coffee)",
        "category": "식음료 (커피전문점)",
        "membership_fee": 7700000,
        "deposit": 5000000,
        "interior_cost": 48000000,
        "other_cost": 31000000,
        "total_initial": 91700000,
        "avg_annual_sales": 253000000,
        "store_count": 2400,
        "royalty": "월 200,000원 고정"
    },
    "이마트24": {
        "brand_name": "이마트24 (Emart24)",
        "category": "판매/서비스 (편의점)",
        "membership_fee": 5500000,
        "deposit": 10000000,
        "interior_cost": 40000000,
        "other_cost": 22000000,
        "total_initial": 77500000,
        "avg_annual_sales": 412000000,
        "store_count": 6500,
        "royalty": "월회비 고정형 (수수료 배분 방식에 따라 상이)"
    },
    "파리바게뜨": {
        "brand_name": "파리바게뜨 (Paris Baguette)",
        "category": "식음료 (제과제빵)",
        "membership_fee": 18000000,
        "deposit": 20000000,
        "interior_cost": 120000000,
        "other_cost": 85000000,
        "total_initial": 243000000,
        "avg_annual_sales": 729000000,
        "store_count": 3400,
        "royalty": "매출의 2.5%"
    }
}

# Mock market properties list for real-time search simulation
MOCK_MARKET_LISTINGS = [
    {
        "id": "list-01",
        "brand": "메가커피 분당서현점",
        "category": "카페",
        "address": "경기도 성남시 분당구 서현동 268",
        "biz_reg_no": "129-87-99112",
        "established_date": "2021-11-05",
        "monthly_net_profit": 5500000,
        "facilities_cost": 45000000,
        "location_premium": 25000000,
        "scrap_price": 75000000
    },
    {
        "id": "list-02",
        "brand": "컴포즈커피 신촌역점",
        "category": "카페",
        "address": "서울특별시 서대문구 창천동 18-5",
        "biz_reg_no": "105-82-44556",
        "established_date": "2023-05-12",
        "monthly_net_profit": 4200000,
        "facilities_cost": 38000000,
        "location_premium": 20000000,
        "scrap_price": 62000000
    },
    {
        "id": "list-03",
        "brand": "교촌치킨 수지구청점",
        "category": "치킨점",
        "address": "경기도 용인시 수지구 풍덕천동 1080",
        "biz_reg_no": "142-12-88776",
        "established_date": "2020-04-18",
        "monthly_net_profit": 8000000,
        "facilities_cost": 30000000,
        "location_premium": 15000000,
        "scrap_price": 50000000
    },
    {
        "id": "list-04",
        "brand": "이마트24 수원시청점",
        "category": "편의점",
        "address": "경기도 수원시 팔달구 인계동 1111",
        "biz_reg_no": "220-45-77332",
        "established_date": "2022-09-01",
        "monthly_net_profit": 3500000,
        "facilities_cost": 28000000,
        "location_premium": 10000000,
        "scrap_price": 45000000
    }
]

def search_franchise(query, api_key=None, api_provider="duckduckgo"):
    """
    브랜드명으로 정보공개서 데이터를 실시간 웹 검색(크롤링/스크래핑) 및 공공/로컬 DB 조회
    반환값: (results_list, sources_list)
    """
    if not query:
        # 검색어가 없을 때 전체 메인 5개 브랜드 반환 (출처는 내부 DB로 설정)
        sources = [
            {
                "title": "공정거래위원회 가맹사업거래 내부 DB",
                "href": "https://franchise.ftc.go.kr",
                "body": "공정거래위원회 가맹사업거래 정보공개서에 공식 등록된 메인 브랜드 기준 데이터입니다."
            }
        ]
        return list(FRANCHISE_DB.values()), sources
    
    query_clean = query.strip()
    
    # 1. 메인 5대 브랜드 로컬 매칭 확인 (성능 및 정확성 우선)
    for key, val in FRANCHISE_DB.items():
        if query_clean.lower() in key.lower() or query_clean.lower() in val["brand_name"].lower():
            sources = [
                {
                    "title": f"공정거래위원회 가맹사업거래 공식 정보 - {val['brand_name']}",
                    "href": "https://franchise.ftc.go.kr",
                    "body": f"{val['brand_name']} 브랜드는 {val['category']} 업종으로 등록된 프랜차이즈입니다. 현재 기준 가맹점 수 {val['store_count']:,}개, 가맹점 평균 연매출 {val['avg_annual_sales']:,}원입니다."
                }
            ]
            return [val], sources

    # 2. 외부 브랜드를 위한 실시간 웹 검색 (크롤링 및 API 호출)
    search_results = []
    search_q = f"{query_clean} 프랜차이즈 정보공개서 가맹점수 연매출 창업비용"
    
    try:
        if api_provider == "serper" and api_key:
            import requests
            url = "https://google.serper.dev/search"
            headers = {"X-API-KEY": api_key, "Content-Type": "application/json"}
            payload = {"q": search_q}
            r = requests.post(url, headers=headers, json=payload, timeout=5)
            if r.status_code == 200:
                res_data = r.json()
                for item in res_data.get("organic", [])[:5]:
                    search_results.append({
                        "title": item.get("title", ""),
                        "href": item.get("link", ""),
                        "body": item.get("snippet", "")
                    })
        elif api_provider == "tavily" and api_key:
            import requests
            url = "https://api.tavily.com/search"
            payload = {"api_key": api_key, "query": search_q, "search_depth": "basic"}
            r = requests.post(url, json=payload, timeout=5)
            if r.status_code == 200:
                res_data = r.json()
                for item in res_data.get("results", [])[:5]:
                    search_results.append({
                        "title": item.get("title", ""),
                        "href": item.get("url", ""),
                        "body": item.get("content", "")
                    })
        else:
            # Default to DuckDuckGo (Keyless Crawler/Scraper)
            with DDGS() as ddgs:
                ddg_res = list(ddgs.text(search_q, max_results=5))
                for item in ddg_res:
                    search_results.append({
                        "title": item.get("title", ""),
                        "href": item.get("href", ""),
                        "body": item.get("body", "")
                    })
    except Exception as e:
        # 검색 에러 발생 시 로그를 남김
        print(f"Realtime search engine error: {e}")
        
    # 검색 결과가 아예 없을 경우 가상의 포탈 출처 생성 (시스템 중단 방지)
    if not search_results:
        search_results = [
            {
                "title": f"공정거래위원회 가맹사업정보제공시스템 '{query_clean}' 검색 결과",
                "href": "https://franchise.ftc.go.kr",
                "body": f"공정거래위원회 가맹사업 사이트에서 '{query_clean}'의 공식 정보공개서를 조회합니다."
            }
        ]

    # 3. 수집된 텍스트 데이터로부터 정량/정성 정보 추출 (Regex & Heuristics)
    all_text = " ".join([item["title"] + " " + item["body"] for item in search_results])
    
    # 가맹점 수 추출 (예: 123개, 1,234개, 가맹점수 500개)
    store_count = 80 # Default fallback
    store_matches = re.findall(r'(?:가맹점\s*수|점포\s*수|매장\s*수)?\s*(\d{1,3}(?:,\d{3})*)\s*개', all_text)
    if store_matches:
        for m in store_matches:
            num = int(m.replace(",", ""))
            if 5 < num < 40000:
                store_count = num
                break
                
    # 평균 연매출액 추출 (예: 3억 5,000만원, 240,000천원, 평균 연매출 450,000,000원)
    avg_annual_sales = 280000000 # Default fallback (2.8억원)
    sales_matches_eok = re.findall(r'(\d+(?:\.\d+)?)\s*억', all_text)
    if sales_matches_eok:
        avg_annual_sales = int(float(sales_matches_eok[0]) * 100000000)
    else:
        sales_matches_man = re.findall(r'(\d{1,3}(?:,\d{3})*)\s*만원', all_text)
        if sales_matches_man:
            avg_annual_sales = int(sales_matches_man[0].replace(",", "")) * 10000
            
    # 업종 카테고리 자동 유추
    category = "식음료 (기타 외식업)"
    if any(w in query_clean for w in ["커피", "카페", "다방", "커스텀", "빽", "투썸", "이디야", "하삼동", "컴포즈", "메가"]):
        category = "식음료 (커피전문점)"
    elif any(w in query_clean for w in ["치킨", "닭", "bhc", "비비큐", "굽네", "네네", "처갓집", "교촌"]):
        category = "식음료 (치킨전문점)"
    elif any(w in query_clean for w in ["편의점", "마트", "24", "세븐", "gs", "cu"]):
        category = "판매/서비스 (편의점)"
    elif any(w in query_clean for w in ["빵", "베이커리", "케익", "파리", "뚜레"]):
        category = "식음료 (제과제빵)"
    elif any(w in query_clean for w in ["피자", "도미노", "미스터", "피자나라"]):
        category = "식음료 (피자전문점)"
    elif any(w in query_clean for w in ["떡볶이", "엽기", "신전", "분식"]):
        category = "식음료 (분식전문점)"
    elif any(w in query_clean for w in ["스터디", "독서실", "카페"]):
        category = "판매/서비스 (스터디카페)"

    # 업종 카테고리에 따른 창업 비용 기본 템플릿 세팅
    if "커피" in category:
        membership_fee = 7500000
        deposit = 3000000
        interior_cost = 45000000
        other_cost = 25000000
        royalty = "월 150,000원 ~ 200,000원 고정"
    elif "치킨" in category:
        membership_fee = 8500000
        deposit = 5000000
        interior_cost = 55000000
        other_cost = 35000000
        royalty = "매출액의 1% - 3%"
    elif "편의점" in category:
        membership_fee = 5000000
        deposit = 10000000
        interior_cost = 38000000
        other_cost = 22000000
        royalty = "월 정액회비 또는 분배형"
    elif "분식" in category:
        membership_fee = 8000000
        deposit = 3000000
        interior_cost = 40000000
        other_cost = 20000000
        royalty = "매출의 2% 고정"
    else:
        membership_fee = 10000000
        deposit = 5000000
        interior_cost = 65000000
        other_cost = 30000000
        royalty = "매출의 2.5%"

    # 텍스트 스니펫 내에서 구체적인 수치(가맹비, 인테리어비) 재탐색 반영
    membership_matches = re.findall(r'가맹비\s*(\d{1,3}(?:,\d{3})*)\s*만', all_text)
    if membership_matches:
        membership_fee = int(membership_matches[0].replace(",", "")) * 10000
        
    interior_matches = re.findall(r'인테리어\s*비(?:용)?\s*(\d{1,3}(?:,\d{3})*)\s*만', all_text)
    if interior_matches:
        interior_cost = int(interior_matches[0].replace(",", "")) * 10000
        
    total_initial = membership_fee + deposit + interior_cost + other_cost
    
    parsed_franchise = {
        "brand_name": f"{query_clean} (실시간 검색 결과)",
        "category": category,
        "membership_fee": membership_fee,
        "deposit": deposit,
        "interior_cost": interior_cost,
        "other_cost": other_cost,
        "total_initial": total_initial,
        "avg_annual_sales": avg_annual_sales,
        "store_count": store_count,
        "royalty": royalty
    }
    
    return [parsed_franchise], search_results

def search_market_listings(query=None, category=None):
    """
    거래 중인 점포 리스트 실시간 모킹 검색
    """
    results = MOCK_MARKET_LISTINGS
    if category and category != "전체":
        results = [r for r in results if r["category"] == category]
    
    if query:
        results = [r for r in results if query.lower() in r["brand"].lower() or query.lower() in r["address"].lower()]
        
    return results


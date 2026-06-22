import numpy as np

def calculate_tangible_value(initial_cost, operating_months, condition_coeff=1.0, base_scrap_rate=0.05):
    """
    유형자산 감가상각 (원가법) 계산
    V_f = P * (1 - t/60) * C_q
    만약 경과 월수(t)가 60개월 이상인 경우, 최소 잔존 가액(base_scrap_rate)을 적용
    """
    # 60개월 기준 감가상각율
    depreciation_rate = max(0.0, 1.0 - (operating_months / 60.0))
    
    # 60개월 경과 시 최소 잔존 가치 보장 (주방 기기 등 고철 가치)
    effective_rate = max(depreciation_rate, base_scrap_rate)
    
    val_facility = initial_cost * effective_rate * condition_coeff
    return round(val_facility, 2)

def calculate_intangible_value(annual_net_profit, discount_rate=0.10, years=3):
    """
    무형자산 영업권리금 (수익환원법) 계산
    V_i = Sum( R_e / (1 + R)^k ) for k = 1 to N
    """
    val_operating = 0.0
    for k in range(1, years + 1):
        val_operating += annual_net_profit / ((1.0 + discount_rate) ** k)
    return round(val_operating, 2)

def calculate_total_valuation(val_facility, val_operating, val_location, val_license):
    """
    총 권리금 = 시설권리금(유형) + 영업권리금(무형) + 바닥권리금(상권) + 허가권리금(행정)
    """
    return round(val_facility + val_operating + val_location + val_license, 2)

def generate_valuation_report(params):
    """
    상세 감정평가 보고서용 데이터 구조 생성
    """
    initial_cost = params.get("initial_cost", 0.0)
    operating_months = params.get("operating_months", 0)
    condition_coeff = params.get("condition_coeff", 1.0)
    
    annual_net_profit = params.get("annual_net_profit", 0.0)
    discount_rate = params.get("discount_rate", 0.10)
    years = params.get("years", 3)
    
    val_location = params.get("val_location", 0.0)
    val_license = params.get("val_license", 0.0)
    
    # 계산 실행
    val_facility = calculate_tangible_value(initial_cost, operating_months, condition_coeff)
    val_operating = calculate_intangible_value(annual_net_profit, discount_rate, years)
    total_val = calculate_total_valuation(val_facility, val_operating, val_location, val_license)
    
    report = {
        "facility_value": val_facility,
        "operating_value": val_operating,
        "location_value": val_location,
        "license_value": val_license,
        "total_valuation": total_val,
        "details": {
            "initial_cost": initial_cost,
            "operating_months": operating_months,
            "condition_coeff": condition_coeff,
            "annual_net_profit": annual_net_profit,
            "discount_rate": discount_rate,
            "years": years
        }
    }
    return report

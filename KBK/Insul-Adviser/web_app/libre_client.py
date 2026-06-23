import datetime
import time
import requests
from typing import Dict, List, Tuple, Union

class LibreLinkUpClient:
    def __init__(self):
        pass

    def get_base_url(self, region: str) -> str:
        r = region.lower().strip()
        if r == "us":
            return "https://api-us.libreview.io"
        elif r == "eu":
            return "https://api-eu.libreview.io"
        elif r == "ap":
            return "https://api-ap.libreview.io"
        elif r == "de":
            return "https://api-de.libreview.io"
        elif r == "fr":
            return "https://api-fr.libreview.io"
        elif r == "jp":
            return "https://api-jp.libreview.io"
        elif r == "ae":
            return "https://api-ae.libreview.io"
        else:
            return "https://api.libreview.io"

    def parse_iso8601(self, date_str: str) -> float:
        try:
            # yyyy-MM-ddTHH:mm:ss
            norm = date_str[:19]
            dt = datetime.datetime.strptime(norm, "%Y-%m-%dT%H:%M:%S")
            # Parse as UTC timestamp (matching Kotlin)
            dt = dt.replace(tzinfo=datetime.timezone.utc)
            return dt.timestamp() * 1000.0
        except Exception:
            return time.time() * 1000.0

    def fetch_recent_glucose(self, email: str, password: str, region: str) -> Dict[str, Union[bool, str, List[Tuple[float, int]], float]]:
        base_url = self.get_base_url(region)
        headers = {
            "Content-Type": "application/json",
            "version": "4.7.0",
            "product": "llu.android"
        }

        try:
            # STEP 1: Login
            login_url = f"{base_url}/llu/auth/login"
            login_body = {
                "email": email,
                "password": password
            }
            login_resp = requests.post(login_url, json=login_body, headers=headers, timeout=8)
            if login_resp.status_code not in (200, 201):
                return {
                    "success": False,
                    "message": f"로그인 실패 (코드: {login_resp.status_code}). 아이디와 비밀번호를 확인해주세요."
                }

            login_data = login_resp.json()
            status = login_data.get("status", -1)
            if status != 0 and "errors" in login_data:
                return {
                    "success": False,
                    "message": "인증 오류: 계정 정보를 찾을 수 없습니다."
                }

            data = login_data.get("data", {})
            auth_ticket = data.get("authTicket", {})
            token = auth_ticket.get("token", "")
            if not token:
                return {
                    "success": False,
                    "message": "인증 토큰이 비어 있습니다."
                }

            # STEP 2: Get Connections
            conn_url = f"{base_url}/llu/connections"
            headers["Authorization"] = f"Bearer {token}"
            conn_resp = requests.get(conn_url, headers=headers, timeout=8)
            if conn_resp.status_code != 200:
                return {
                    "success": False,
                    "message": f"연결 목록 조회 실패 (코드: {conn_resp.status_code})"
                }

            conn_data = conn_resp.json()
            conn_list = conn_data.get("data", [])
            if not conn_list:
                return {
                    "success": False,
                    "message": "연동된 CGM 환자 프로필이 없습니다. LibreLinkUp 앱에서 공유 초청을 먼저 승인해주세요."
                }

            patient_id = ""
            for item in conn_list:
                pid = item.get("patientId", "")
                if pid:
                    patient_id = pid
                    break

            if not patient_id:
                return {
                    "success": False,
                    "message": "환자 ID를 찾을 수 없습니다."
                }

            # STEP 3: Fetch Glucose Graph Data
            graph_url = f"{base_url}/llu/connections/{patient_id}/graph"
            graph_resp = requests.get(graph_url, headers=headers, timeout=8)
            if graph_resp.status_code != 200:
                return {
                    "success": False,
                    "message": f"혈당 데이터 조회 실패 (코드: {graph_resp.status_code})"
                }

            graph_json = graph_resp.json()
            graph_data_obj = graph_json.get("data", {})
            graph_arr = graph_data_obj.get("graphData", [])

            readings = []
            sum_glucose = 0
            count_readings = 0

            for item in graph_arr:
                val = item.get("Value", -1)
                ts_str = item.get("Timestamp", "")
                if val > 0 and ts_str:
                    time_ms = self.parse_iso8601(ts_str)
                    readings.append((time_ms, val))
                    sum_glucose += val
                    count_readings += 1

            if not readings:
                return {
                    "success": False,
                    "message": "최근 등록된 혈당 센서 기록이 없습니다."
                }

            # Sort chronologically
            readings.sort(key=lambda x: x[0])

            avg_glucose = sum_glucose / count_readings
            est_hba1c = (avg_glucose + 46.7) / 28.7

            return {
                "success": True,
                "readings": readings,
                "avg_glucose": avg_glucose,
                "est_hba1c": est_hba1c
            }

        except Exception as e:
            return {
                "success": False,
                "message": f"네트워크 오류: {str(e)}"
            }

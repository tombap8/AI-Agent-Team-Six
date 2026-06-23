import math
import re
from collections import Counter

# 1. RAG Knowledge Base documents (상가임대차법, 권리금 평가법, 계약 유의사항 등)
KNOWLEDGE_BASE = [
    {
        "id": 1,
        "category": "법률/임대차",
        "title": "상가임대차 권리금 회수 보호 기간",
        "text": "상가임대차보호법에 따르면 임대인은 임대차기간이 끝나기 6개월 전부터 임대차 종료 시까지 임차인이 주선한 신규임차인이 되려는 자로부터 권리금을 지급받는 것을 방해해서는 안 되며, 이를 위반하여 손해가 발생한 경우 임차인에게 손해배상 책임을 집니다."
    },
    {
        "id": 2,
        "category": "계약 실무",
        "title": "표준임대차 권리금 계약서 세분화",
        "text": "국토교통부 표준임대차 권리금 계약서 작성 시, 영업 권리금(고객 단골 및 영업 노하우), 시설 권리금(주방 집기, 인테리어 감가상각), 바닥 권리금(상권 위치 프리미엄), 허가 권리금(합법 인허가 행정 라이선스) 등 가치 항목을 정확하게 구분하여 특약 조건으로 체결하는 것이 분쟁을 예방하는 지름길입니다."
    },
    {
        "id": 3,
        "category": "거래 보안",
        "title": "국세청 사업자 진위 조회 및 허위매물 사기 방지",
        "text": "상가 양도양수 시 실제 소유주 확인을 위해 국세청 사업자등록정보 진위확인 API를 통해 사업자번호, 대표자명, 상호명, 개업일자를 공공 데이터 원장과 실시간 대조하여 1글자라도 다르면 즉각 차단해야 합니다. 계속사업자 상태인지, 휴폐업 상태인지 조회하여 대리인 위조 계약 사기를 선제 차단할 수 있습니다."
    },
    {
        "id": 4,
        "category": "감정평가/시설",
        "title": "시설 권리금 60개월 감가상각법",
        "text": "주방 시설, 냉난방기, 인테리어 등 시설 권리금은 실무 및 세법상 5년(60개월)의 가치 감쇄 기간을 적용하는 원가법 계산이 기준입니다. 잔존 가치 계산식은 V_f = P * (1 - t/60) * C_q 이며, 설치 후 경과 개월 수가 60개월이 넘더라도 5% 내외의 최소 잔존 가액(고철 가치)은 보존하는 것이 원칙입니다."
    },
    {
        "id": 5,
        "category": "감정평가/영업",
        "title": "영업 권리금 수익환원법 산출 원리",
        "text": "영업 권리금은 점포의 브랜드 가치 및 노하우를 정량화하는 것으로, 세무서 신고 소득금액 또는 카드 매출 총이익에서 임차료, 인건비, 자가 인건비 대체비용 등을 차감한 '순 영업이익(R_e)'에 적정 할인율(R, 보통 10%)을 적용해 향후 2~5년간의 가치를 현재가치로 환원 합산하여 구합니다."
    },
    {
        "id": 6,
        "category": "창업/비교",
        "title": "공정위 정보공개서 대조 검증",
        "text": "프랜차이즈 가맹 창업을 진행할 때는 공정거래위원회 가맹사업거래 사이트에 공식 등록된 브랜드 정보공개서를 바탕으로 가맹점 평균 연매출, 가맹금, 보증금, 인테리어 평균 비용 및 동일 업종의 개폐업률 추이를 빅데이터로 비교하여 창업의 합리성을 검증해야 합니다."
    },
    {
        "id": 7,
        "category": "에스크로",
        "title": "안전 거래를 위한 에스크로 제도",
        "text": "점포 권리 계약 시 발생하는 계약금 유실 사고를 막기 위해, 매수인이 결제한 권리금과 계약금을 제3의 가상 에스크로 계좌에 보존한 뒤 사업자등록 실시간 진위 검증 및 현장 실사 및 인허가 양도 절차가 완벽히 마무리되는 시점에 매도인에게 정산 입금되도록 거래 안전 장치를 설계해야 합니다."
    }
]

# Simple TF-IDF implementation in pure Python
class TFIDFSearch:
    def __init__(self, docs):
        self.docs = docs
        self.doc_count = len(docs)
        self.vocab = set()
        self.doc_tokens = []
        self.idf = {}
        self.doc_vectors = []
        self._build_index()

    def _tokenize(self, text):
        # Convert to lowercase and match words
        words = re.findall(r'[a-zA-Z0-9가-힣]+', text.lower())
        return words

    def _build_index(self):
        # Tokenize all documents
        for doc in self.docs:
            tokens = self._tokenize(doc["text"] + " " + doc["title"])
            self.doc_tokens.append(tokens)
            self.vocab.update(tokens)
        
        # Calculate IDF
        for term in self.vocab:
            containing_docs = sum(1 for tokens in self.doc_tokens if term in tokens)
            self.idf[term] = math.log((1 + self.doc_count) / (1 + containing_docs)) + 1
            
        # Calculate TF-IDF vectors for documents
        for tokens in self.doc_tokens:
            vector = {}
            term_counts = Counter(tokens)
            total_terms = len(tokens) if len(tokens) > 0 else 1
            for term, count in term_counts.items():
                tf = count / total_terms
                vector[term] = tf * self.idf[term]
            self.doc_vectors.append(vector)

    def _cosine_similarity(self, vec1, vec2):
        intersection = set(vec1.keys()) & set(vec2.keys())
        numerator = sum(vec1[x] * vec2[x] for x in intersection)
        
        sum1 = sum(vec1[x] ** 2 for x in vec1.keys())
        sum2 = sum(vec2[x] ** 2 for x in vec2.keys())
        
        denominator = math.sqrt(sum1) * math.sqrt(sum2)
        if not denominator:
            return 0.0
        return numerator / denominator

    def search(self, query, top_k=2):
        query_tokens = self._tokenize(query)
        query_vector = {}
        term_counts = Counter(query_tokens)
        total_terms = len(query_tokens) if len(query_tokens) > 0 else 1
        
        for term, count in term_counts.items():
            if term in self.vocab:
                tf = count / total_terms
                query_vector[term] = tf * self.idf[term]
                
        if not query_vector:
            return []
            
        results = []
        for idx, doc_vector in enumerate(self.doc_vectors):
            score = self._cosine_similarity(query_vector, doc_vector)
            if score > 0:
                results.append((score, self.docs[idx]))
                
        # Sort by score descending
        results.sort(key=lambda x: x[0], reverse=True)
        return results[:top_k]

# Initialize search engine
search_engine = TFIDFSearch(KNOWLEDGE_BASE)

def generate_rag_response(user_query):
    """
    RAG 검색을 진행하고 답변을 생성
    """
    matches = search_engine.search(user_query, top_k=2)
    
    if not matches:
        return (
            "죄송합니다. 질문하신 내용과 관련된 법률이나 실무 매뉴얼을 데이터베이스에서 찾을 수 없습니다. "
            "권리금 계산 공식, 사업자 진위 확인, 에스크로, 프랜차이즈 비교 등에 대해 질문해주시면 자세히 답변해드리겠습니다.",
            []
        )
        
    # Construct Context
    contexts = []
    sources = []
    for score, doc in matches:
        contexts.append(f"[{doc['title']}] {doc['text']}")
        sources.append(doc)
        
    context_str = "\n\n".join(contexts)
    
    # Simple templates mapping to simulate intelligent text synthesis
    system_prompt = (
        f"당신은 대한민국 상가 점포 창업 및 양도양수 전문 AI 도우미 에이전트입니다. "
        f"다음 참고 자료를 기초로 하여 친절하고 신뢰감 높은 답변을 작성해주세요.\n\n"
        f"[참고 자료]\n{context_str}"
    )
    
    # Custom synthesized answers based on high matches
    best_doc_id = matches[0][1]["id"]
    
    # Synthesized Answer Mapping
    if best_doc_id == 1:
        answer = (
            "🏠 **상가임대차보호법 권리금 회수 보호 기간 안내**\n\n"
            "현재 상가임대차보호법에 따라 임차인은 계약 만료 **6개월 전부터 임대차 종료 시까지** 권리금 회수를 법적으로 보호받습니다.\n\n"
            "이 기간 내에 임차인이 새로운 임차인을 주선해 오면 임대인은 정당한 사유(예: 상가 건물의 파손 위험, 1년 6개월 이상 비영리 목적으로 사용 등) 없이 "
            "권리금 계약 체결을 거절하거나 방해해서는 안 됩니다. 방해 행위가 인정될 경우 임차인은 임대인을 상대로 권리금 상당의 손해배상을 청구할 수 있습니다.\n\n"
            "💡 **주의**: 반드시 임대차 계약 종료 6개월 전 시점부터 적극적으로 새로운 양수인을 구하고 계약서 주선 의사를 증빙(내용증명 등)으로 남겨두시는 것이 안전합니다."
        )
    elif best_doc_id == 2:
        answer = (
            "📑 **임대차 권리금 표준 계약서 및 작성 요령 안내**\n\n"
            "점포 거래 시 가장 분쟁이 잦은 영역이 바로 '권리금의 상세 구분'입니다. 국토교통부 고시 표준 계약서 작성을 필수로 진행하시는 것을 강력히 권장합니다.\n\n"
            "계약 시 다음과 같이 가치 평가 항목을 명확하게 쪼개서 세부 특약에 기재해야 합니다:\n"
            "1. **시설 권리금**: 인테리어, 주방 집기, 가구 및 냉난방설비에 대한 잔존가치\n"
            "2. **영업 권리금**: 단골 확보 현황, 매출 기록, 브랜드 영업 가치 및 운영 노하우\n"
            "3. **바닥 권리금**: 유동인구 입지 프리미엄\n"
            "4. **허가 권리금**: 24시간 특별 인허가, 환경 시설 인허가 등 승계가 까다로운 행정 자산\n\n"
            "이 중 어떤 항목이 권리금에 포함되었는지 명확히 기록해두지 않으면 계약 취소나 하자 보수 시 분쟁 조정이 극도로 어려워집니다."
        )
    elif best_doc_id == 3:
        answer = (
            "🔒 **허위매물 및 명의 도용 계약 사기 예방 가이드**\n\n"
            "최근 발생한 프랜차이즈 양도 사기 사건은 타인의 사업자등록증이나 신분증을 위조하여 대리 점주 행세를 하며 보증금/권리금을 가로채고 도주하는 패턴이 많습니다.\n\n"
            "이를 방지하기 위해 저희 플랫폼은 **국세청 사업자등록 진위확인 API** 연동 시스템을 기본 탑재하고 있습니다:\n"
            "- 매도인이 등록한 **사업자번호, 대표자명, 상호명, 개업일자**가 홈택스 공적 데이터 원장과 단 한 글자라도 일치하지 않는 경우 승인이 원천 차단됩니다.\n"
            "- 계약 체결 당일에도 API 상태 조회를 작동시켜 해당 점포가 현재 **계속사업자** 인지, 혹은 **폐업/휴업** 상태인지 실시간 체크하여 휴폐업 상태인 유령 매물에 돈을 지불하는 실수를 방지합니다."
        )
    elif best_doc_id == 4:
        answer = (
            "🔧 **시설 권리금 감가상각 공식 및 원가법 가이드**\n\n"
            "인테리어 및 시설의 잔존가치 평가는 대한민국 감정평가 실무 규정의 '원가법'에 기초하여 계산합니다.\n\n"
            "저희 플랫폼의 시설권리금 계산 원리는 다음과 같습니다:\n"
            "$$V_f = P \\times (1 - t/60) \\times C_q$$\n"
            "- **재조달원가(P)**: 시설/인테리어에 지출된 최초 설치 실비입니다.\n"
            "- **경과 개월 수(t)**: 감쇄 기간은 **5년(60개월)** 기준입니다. 매달 1/60씩 가치가 차감됩니다.\n"
            "- **정성 보정 계수($C_q$)**: 현장 실사 및 보존 상태에 따라 다르게 지정됩니다. 관리가 우수하면 1.0에 가까우며 장비 교체가 필요하면 0.0으로 수렴합니다.\n\n"
            "⚠️ **참고**: 연식이 5년을 초과하더라도 실제 구동이 보장되는 주방 화구나 냉난방기 등은 완전히 0원으로 처리하지 않고, 최초 금액의 **5% 수준의 고철 잔존 가치**를 최소 보장하여 양도/양수인 간의 원만한 합의를 유도합니다."
        )
    elif best_doc_id == 5:
        answer = (
            "📈 **영업 권리금 계산 공식 및 수익가치 산정법**\n\n"
            "영업 권리금은 상권 매출이나 브랜드 파워 등 보이지 않는 무형 영업권 가치를 구하는 것으로, 감정평가 상 '수익환원법'에 근거합니다.\n\n"
            "**핵심 산식**:\n"
            "$$V_i = \\sum_{k=1}^N \\frac{R_e}{(1 + R)^k}$$\n"
            "1. **순 영업이익($R_e$)**: 점포의 월평균 실질 소득(총 카드 매출 - 임대료 - 재료비 - 세무경비)에서 점주 본인의 대체 인건비(노동 대가)까지 제하고 남는 순수 영업이익을 구합니다.\n"
            "2. **할인율(R)**: 점포 리스크 및 변동 이자율을 반영하는 가이드라인 할인율로 보통 **10%**로 잡습니다.\n"
            "3. **존속 년수(N)**: 영업 가치가 이전되어 유지될 기간으로 분쟁 실무상 **2년~3년**을 기본 설정합니다.\n\n"
            "이 공식을 적용하면 단순 호가에 끌려다니지 않고 객관적이고 공정한 시장 가치 영업 프리미엄을 역산해 낼 수 있습니다."
        )
    elif best_doc_id == 6:
        answer = (
            "📊 **공정위 정보공개서 기반 프랜차이즈 창업 타당성 검증**\n\n"
            "가맹 브랜드를 인수하거나 신규 출점할 때 가장 객관적인 기준은 **공정거래위원회 가맹사업거래 정보공개서**입니다.\n\n"
            "체크해야 할 3대 주요 지표:\n"
            "1. **평균 연매출액**: 본사가 주장하는 매출액이 실제 전국 가맹점 평균 공시액과 맞는지 비교합니다.\n"
            "2. **초기 창업 비용**: 가맹비, 교육비, 평당 인테리어 비용 등 실제 지불해야 할 필수 총자본금을 파악합니다.\n"
            "3. **개폐업 추이**: 가입 브랜드의 매년 신규 개점 수 대비 폐점 비중을 계산하여 브랜드 안정성을 분석합니다.\n\n"
            "저희 플랫폼의 '실시간 정보공개서 비교 툴'을 통해 각 브랜드의 공시 수치를 정밀하게 비교하여 안정성을 사전에 확인해보세요."
        )
    else:
        answer = (
            "💳 **에스크로(안심 거래) 및 수수료 정산 서비스 안내**\n\n"
            "양도양수 계약 후 계약금이나 권리금을 지불할 때 사기 방지를 위해 안심 거래 **에스크로(Escrow) 가상 계좌**를 연동합니다.\n\n"
            "- 계약금은 신규 영업 인허가증 발급 및 사업자등록 이전 절차가 공식적으로 검증 완료될 때까지 에스크로 계좌에 안전하게 예치됩니다.\n"
            "- 행정 이전이 승인되면 안전하게 매도자 계좌로 자동 정산 입금됩니다.\n"
            "- 계산 및 이체 과정에서 발생하는 합법적 권리 중개 수수료율(법정 상한 3%~5% 범위 내 협의)도 결제 시스템에서 즉각 자동 정산됩니다."
        )
        
    return answer, sources

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

    def _clean_korean_suffix(self, word):
        # Strip common postpositions (조사) at the end of Korean words
        suffixes = ['은', '는', '이', '가', '을', '를', '의', '로', '으로', '에', '에서', '와', '과', '도', '만', '하고', '이며', '입니다', '한다', '했다', '요', '가요', '나요', '인가요', '인가요?']
        suffixes.sort(key=len, reverse=True)
        for suffix in suffixes:
            if word.endswith(suffix) and len(word) > len(suffix):
                return word[:-len(suffix)]
        return word

    def _tokenize(self, text):
        # Convert to lowercase and match words
        words = re.findall(r'[a-zA-Z0-9가-힣]+', text.lower())
        tokens = []
        for w in words:
            tokens.append(w)
            stripped = self._clean_korean_suffix(w)
            if stripped != w:
                tokens.append(stripped)
            
            # Generate bigrams for Korean parts
            if any(ord('가') <= ord(char) <= ord('힣') for char in w):
                for i in range(len(w) - 1):
                    tokens.append(w[i:i+2])
        return tokens

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
            "<p>죄송합니다. 질문하신 내용과 관련된 법률이나 실무 매뉴얼을 데이터베이스에서 찾을 수 없습니다. "
            "권리금 계산 공식, 사업자 진위 확인, 에스크로, 프랜차이즈 비교 등에 대해 질문해주시면 자세히 답변해드리겠습니다.</p>",
            []
        )
        
    # Construct Context
    contexts = []
    sources = []
    for score, doc in matches:
        contexts.append(f"[{doc['title']}] {doc['text']}")
        sources.append(doc)
        
    # Custom synthesized answers based on high matches
    best_doc_id = matches[0][1]["id"]
    
    # Synthesized Answer Mapping (HTML format)
    if best_doc_id == 1:
        answer = (
            '<h3 style="margin-top:0; color:#4F46E5; font-family:\'Outfit\';">🏠 상가임대차 권리금 회수 보호 기간 안내</h3>'
            '<p>상가임대차보호법에 따라 임차인은 계약 종료 전 <strong>안전한 권리금 회수 기회</strong>를 법적으로 보호받습니다.</p>'
            '<div style="background: rgba(79, 70, 229, 0.05); padding: 15px; border-radius: 10px; border-left: 4px solid #4F46E5; margin: 15px 0;">'
            '    <strong>법적 보호 기간:</strong> 임대차 계약 기간 만료 <strong>6개월 전부터 임대차 계약 종료 시까지</strong>'
            '</div>'
            '<h4 style="color:#0D9488; margin: 20px 0 8px 0;">💡 핵심 주의 사항 및 대응 전략</h4>'
            '<ul style="padding-left: 20px; line-height: 1.8;">'
            '    <li><strong>신규 임차인 주선 의무:</strong> 임차인은 상기 보호 기간 내에 새로운 임차인을 구해 임대인에게 적극적으로 주선해야 합니다. 주선 사실은 <em>내용증명</em>이나 문자메시지 등으로 객관적인 증빙을 남겨두는 것이 안전합니다.</li>'
            '    <li><strong>임대인의 방해 행위 금지:</strong> 임대인은 정당한 사유 없이 신규 임차인과의 계약을 거절하거나, 터무니없이 높은 보증금/월세를 요구해 권리금 계약을 방해해서는 안 됩니다.</li>'
            '    <li><strong>손해배상 청구:</strong> 임대인의 방해로 권리금을 회수하지 못해 손해가 발생한 경우, 계약 종료 후 <strong>3년 이내</strong>에 임대인을 상대로 권리금 상당의 손해배상을 청구할 수 있습니다. (배상액 한도는 기존 권리금과 신규 임차인이 지급하려는 권리금 중 낮은 금액 기준)</li>'
            '</ul>'
        )
    elif best_doc_id == 2:
        answer = (
            '<h3 style="margin-top:0; color:#4F46E5; font-family:\'Outfit\';">📑 권리금 계약서 작성 요령 및 항목 구분</h3>'
            '<p>점포 양도양수 시 가장 잦은 분쟁 요인은 권리금의 세부 항목이 불명확하기 때문입니다. 국토교통부 고시 <strong>\'표준 권리금 계약서\'</strong> 작성을 기본으로 하되, 아래 4가지 항목을 상세히 나누어 명시해야 합니다.</p>'
            '<table style="width:100%; border-collapse:collapse; margin:15px 0; font-size:0.9rem;">'
            '    <thead>'
            '        <tr style="background:#F1F5F9; border-bottom:2px solid #CBD5E1; text-align:left;">'
            '            <th style="padding:10px; border:1px solid #E2E8F0;">권리금 구분</th>'
            '            <th style="padding:10px; border:1px solid #E2E8F0;">주요 평가 대상</th>'
            '            <th style="padding:10px; border:1px solid #E2E8F0;">리스크 관리/특약 작성 팁</th>'
            '        </tr>'
            '    </thead>'
            '    <tbody>'
            '        <tr>'
            '            <td style="padding:10px; border:1px solid #E2E8F0; font-weight:bold;">영업 권리금</td>'
            '            <td style="padding:10px; border:1px solid #E2E8F0;">고객 단골수, 상호 인지도, 영업 노하우 등 무형 가치</td>'
            '            <td style="padding:10px; border:1px solid #E2E8F0;">포스(POS) 매출자료 및 세무 신고 내역 실사 대조 특약</td>'
            '        </tr>'
            '        <tr style="background:#F8FAFC;">'
            '            <td style="padding:10px; border:1px solid #E2E8F0; font-weight:bold;">시설 권리금</td>'
            '            <td style="padding:10px; border:1px solid #E2E8F0;">인테리어, 주방 집기, 냉난방 설비 등 유형 자산</td>'
            '            <td style="padding:10px; border:1px solid #E2E8F0;">5년 감가상각 적용 잔존가 및 인수인계 시 정상작동 담보 특약</td>'
            '        </tr>'
            '        <tr>'
            '            <td style="padding:10px; border:1px solid #E2E8F0; font-weight:bold;">바닥 권리금</td>'
            '            <td style="padding:10px; border:1px solid #E2E8F0;">상권 입지 프리미엄, 유동인구에 따른 장소적 이점</td>'
            '            <td style="padding:10px; border:1px solid #E2E8F0;">인근 동종 업계의 권리금 실거래 사례 비교 검토</td>'
            '        </tr>'
            '        <tr style="background:#F8FAFC;">'
            '            <td style="padding:10px; border:1px solid #E2E8F0; font-weight:bold;">허가 권리금</td>'
            '            <td style="padding:10px; border:1px solid #E2E8F0;">합법 인허가, 특수 업태 행정 라이선스 등</td>'
            '            <td style="padding:10px; border:1px solid #E2E8F0;">관공서 용도변경 및 인허가 승계 실패 시 계약금 반환 특약</td>'
            '        </tr>'
            '    </tbody>'
            '</table>'
            '<p style="font-size:0.9rem; color:#475569;">※ 계약서 작성 시 각 항목별 합산 금액과 양수인에게 인수인계할 물품 목록(비품 명세서)을 서면으로 첨부하는 것이 안전합니다.</p>'
        )
    elif best_doc_id == 3:
        answer = (
            '<h3 style="margin-top:0; color:#4F46E5; font-family:\'Outfit\';">🔒 사업자 진위 확인 및 허위매물 사기 방지</h3>'
            '<p>양도양수 계약 전 반드시 점포의 소유권자와 사업자등록 상태를 검증하여 명의 도용 계약 사기를 예방해야 합니다.</p>'
            '<div style="background: rgba(239, 68, 68, 0.05); padding: 15px; border-radius: 10px; border-left: 4px solid #EF4444; margin: 15px 0;">'
            '    <strong>핵심 예방 장치: 국세청 사업자등록정보 진위확인 API 연동</strong><br>'
            '    홈택스 공적 데이터 원장과 실시간 연동하여 매도인이 제공한 <strong>사업자번호, 대표자명, 상호명, 개업일자</strong>를 1글자 단위로 대조 검증합니다.'
            '</div>'
            '<h4 style="color:#0D9488; margin: 20px 0 8px 0;">🛡️ 안전 계약을 위한 3단계 자가 체크리스트</h4>'
            '<ol style="padding-left: 20px; line-height: 1.8;">'
            '    <li><strong>사업자등록 상태 조회:</strong> 거래 당일 시점에도 대상 점포가 \'계속사업자\' 상태인지, 아니면 이미 \'폐업\' 또는 \'휴업\' 상태인지 확인합니다. (폐업된 유령 매물 방지)</li>'
            '    <li><strong>임대차계약 원본 확인:</strong> 건물주와 현재 매도인 간의 임대차계약서 원본, 건물 등기부등본상의 임대인 신원과 실제 인적사항이 일치하는지 반드시 대조하십시오.</li>'
            '    <li><strong>대리 계약 시 위임장 검증:</strong> 매도인 본인이 아닌 대리인이 참석할 경우, 인감증명서가 첨부된 위임장을 확인하고 매도인 본인에게 직접 유선 및 영상통화로 계약 위임 의사를 재확인하십시오.</li>'
            '</ol>'
        )
    elif best_doc_id == 4:
        answer = (
            '<h3 style="margin-top:0; color:#4F46E5; font-family:\'Outfit\';">🔧 시설 권리금 감가상각 공식 및 원가법 평가</h3>'
            '<p>인테리어 및 주방 설비 등 유형 자산의 가치는 대한민국 감정평가 및 세법 기준에 의거하여 <strong>\'원가법\'</strong>으로 산정합니다.</p>'
            '<div style="background: rgba(13, 148, 136, 0.05); padding: 15px; border-radius: 10px; border-left: 4px solid #0D9488; margin: 15px 0; text-align:center;">'
            '    <span style="font-size: 1.15rem; font-weight: bold; font-family:\'Outfit\';">시설 권리 잔존가치 계산 공식 (원가법)</span><br>'
            '    <div style="font-size:1.4rem; margin:10px 0; font-weight:bold; color:#4F46E5;">'
            '        V<sub>f</sub> = P &times; (1 - t / 60) &times; C<sub>q</sub>'
            '    </div>'
            '    <div style="text-align:left; max-width:550px; margin:0 auto; font-size:0.9rem; line-height:1.6; color: var(--text-color);">'
            '        • <strong>재조달원가(P):</strong> 설비 및 인테리어를 신규로 재구축할 때 드는 합리적인 실비 가격<br>'
            '        • <strong>경과 개월수(t):</strong> 설치완료 시점부터 평가 시점까지 경과한 개월 수 (세법 기준 감가상각 기간 <strong>5년/60개월</strong> 한도)<br>'
            '        • <strong>보정계수(C<sub>q</sub>):</strong> 관리 상태 및 작동 여부에 따른 정성적 보정값 (우수 1.0 ~ 불량 0.0)'
            '    </div>'
            '</div>'
            '<h4 style="color:#0D9488; margin: 20px 0 8px 0;">💡 실무적 적용 규칙</h4>'
            '<ul style="padding-left: 20px; line-height: 1.8;">'
            '    <li><strong>최소 잔존 가액 보존 (고철 가치):</strong> 설치 후 경과 개월 수(t)가 60개월을 초과하더라도 실제로 정상 작동되고 사용 가치가 있는 주요 주방 기기, 냉난방 설비 등은 최초 취득 원가의 <strong>5% 내외의 잔존가치</strong>를 인정해 주는 것이 실무적인 원칙입니다.</li>'
            '    <li><strong>유형 자산 실사 목록표 첨부:</strong> 분쟁을 방지하기 위해 매물 인계 목록표를 작성하고 작동 상태를 직접 확인한 뒤 확인 서명을 명세서에 첨부해야 합니다.</li>'
            '</ul>'
        )
    elif best_doc_id == 5:
        answer = (
            '<h3 style="margin-top:0; color:#4F46E5; font-family:\'Outfit\';">📈 영업권리금 수익환원법의 순수익 가치 전환 원리</h3>'
            '<p>영업권리금 평가에서 <strong>\'수익환원법\'</strong>은 대상 점포가 장래에 창출할 것으로 기대되는 순수익(초과이익)을 현재가치로 할인하여 무형자산(영업권)의 가치를 산정하는 감정평가 실무 기준이자 가장 과학적인 방식입니다.</p>'
            '<div style="background: rgba(79, 70, 229, 0.05); padding: 20px; border-radius: 12px; border-left: 5px solid #4F46E5; margin: 15px 0;">'
            '    <h4 style="margin: 0 0 10px 0; color:#4F46E5; font-size:1.05rem;">🎯 핵심 개념: 미래의 돈을 현재 가치로 바꾸는 법</h4>'
            '    <p style="margin: 0; font-size:0.95rem; line-height:1.6;">'
            '        "수익환원법"의 대전제는 <strong>\'오늘의 1원\'이 \'내일의 1원\'보다 가치가 크다</strong>는 시간선호 및 위험 가치를 반영하는 것입니다. '
            '        장래 매년 발생할 순수익을 이자율에 상응하는 <strong>할인율(R)</strong>로 매년 복리 할인하여 현재 시점의 가치로 다 더합니다.'
            '    </p>'
            '</div>'
            '<h4 style="color:#0D9488; margin: 20px 0 10px 0;">📐 가치 환원 공식 (Mathematical Model)</h4>'
            '<div style="background:#F8FAFC; border:1px solid #E2E8F0; padding:20px; border-radius:10px; text-align:center; margin-bottom:20px;">'
            '    <div style="font-size: 1.5rem; font-weight: bold; font-family:\'Outfit\'; margin-bottom:10px; color:#1E293B;">'
            '        V<sub>i</sub> = <span style="font-size: 1.8rem; vertical-align: middle;">∑</span><sub>k=1</sub><sup>N</sup> <div style="display: inline-block; vertical-align: middle; text-align: center;"><div style="border-bottom: 1px solid #1E293B; padding: 0 5px;">R<sub>e</sub></div><div>(1 + R)<sup>k</sup></div></div>'
            '    </div>'
            '    <div style="text-align:left; max-width:550px; margin:0 auto; font-size:0.9rem; line-height:1.6; color:#475569;">'
            '        • <strong>V<sub>i</sub>:</strong> 산정된 무형자산 영업권리금 가치<br>'
            '        • <strong>R<sub>e</sub>:</strong> 자가 인건비 및 유형자산 기여분을 조정한 <strong>연간 순 영업이익(초과 이익)</strong><br>'
            '        • <strong>R:</strong> 상권 리스크 및 금리를 반영한 <strong>가이드라인 할인율</strong> (감정평가 실무상 통상 <strong>10%</strong> 적용)<br>'
            '        • <strong>N:</strong> 영업 노하우 및 단골 고객 유효 지속 기간인 <strong>존속 년수</strong> (실무상 <strong>2년 ~ 5년</strong> 적용)'
            '    </div>'
            '</div>'
            '<h4 style="color:#0D9488; margin: 20px 0 10px 0;">🔍 1단계: 순수익(초과이익, R<sub>e</sub>)은 어떻게 도출하나요?</h4>'
            '<p style="line-height:1.7;">'
            '    일반적인 회계 장부상 영업이익에서 <strong>무형자산(점포 노하우 및 신용) 외의 요소가 기여한 몫을 공제</strong>하여 정밀 산정합니다.'
            '</p>'
            '<ul style="padding-left: 20px; line-height: 1.8; margin-bottom: 20px;">'
            '    <li><strong>점주 대체 인건비 공제:</strong> 점주가 직접 노동하여 아낀 인건비는 자본적 순이익이 아니므로, 동종업계 평균 급여 수준의 <em>점주 본인 대체 인건비</em>를 비용으로 공제합니다.</li>'
            '    <li><strong>유형자산(시설 등) 기여분 공제:</strong> 고가 장비나 인테리어로 인해 발생한 이익을 빼고 오직 브랜드 및 서비스 가치에 따른 초과이익만 남깁니다.</li>'
            '    <li><strong>비정상적 비용 조정:</strong> 사적 세무 처리 비용이나 비정상적인 일회성 이익을 제외하여 \'정상 영업이익\'으로 보정합니다.</li>'
            '</ul>'
            '<h4 style="color:#0D9488; margin: 20px 0 10px 0;">💵 2단계: 구체적인 계산 예시 (시뮬레이션)</h4>'
            '<p>자가 인건비 및 경비를 공제한 <strong>연간 순 영업이익(R<sub>e</sub>)이 3,000만 원</strong>이고, <strong>할인율(R)이 10%</strong>이며, 영업권 <strong>존속 기간(N)이 3년</strong>이라고 가정할 때의 변환 과정입니다.</p>'
            '<table style="width:100%; border-collapse:collapse; margin:15px 0; font-size:0.9rem; text-align:center;">'
            '    <thead>'
            '        <tr style="background:#F1F5F9; border-bottom:2px solid #CBD5E1;">'
            '            <th style="padding:10px; border:1px solid #E2E8F0;">연차 (k)</th>'
            '            <th style="padding:10px; border:1px solid #E2E8F0;">미래 순수익 (R<sub>e</sub>)</th>'
            '            <th style="padding:10px; border:1px solid #E2E8F0;">할인 수식 (1 + R)<sup>k</sup></th>'
            '            <th style="padding:10px; border:1px solid #E2E8F0;">할인율 적용 계산</th>'
            '            <th style="padding:10px; border:1px solid #E2E8F0; font-weight:bold; color:#4F46E5;">현재 가치 환산액 (PV)</th>'
            '        </tr>'
            '    </thead>'
            '    <tbody>'
            '        <tr>'
            '            <td style="padding:10px; border:1px solid #E2E8F0; font-weight:bold;">1년차 (k=1)</td>'
            '            <td style="padding:10px; border:1px solid #E2E8F0;">3,000만 원</td>'
            '            <td style="padding:10px; border:1px solid #E2E8F0;">1.1<sup>1</sup> = 1.100</td>'
            '            <td style="padding:10px; border:1px solid #E2E8F0;">30,000,000 / 1.1</td>'
            '            <td style="padding:10px; border:1px solid #E2E8F0; font-weight:bold; color:#4F46E5;">2,727만 원</td>'
            '        </tr>'
            '        <tr style="background:#F8FAFC;">'
            '            <td style="padding:10px; border:1px solid #E2E8F0; font-weight:bold;">2년차 (k=2)</td>'
            '            <td style="padding:10px; border:1px solid #E2E8F0;">3,000만 원</td>'
            '            <td style="padding:10px; border:1px solid #E2E8F0;">1.1<sup>2</sup> = 1.210</td>'
            '            <td style="padding:10px; border:1px solid #E2E8F0;">30,000,000 / 1.21</td>'
            '            <td style="padding:10px; border:1px solid #E2E8F0; font-weight:bold; color:#4F46E5;">2,479만 원</td>'
            '        </tr>'
            '        <tr>'
            '            <td style="padding:10px; border:1px solid #E2E8F0; font-weight:bold;">3년차 (k=3)</td>'
            '            <td style="padding:10px; border:1px solid #E2E8F0;">3,000만 원</td>'
            '            <td style="padding:10px; border:1px solid #E2E8F0;">1.1<sup>3</sup> = 1.331</td>'
            '            <td style="padding:10px; border:1px solid #E2E8F0;">30,000,000 / 1.331</td>'
            '            <td style="padding:10px; border:1px solid #E2E8F0; font-weight:bold; color:#4F46E5;">2,254만 원</td>'
            '        </tr>'
            '        <tr style="background:#EEF2FF; font-weight:bold; border-top: 2px solid #6366F1;">'
            '            <td colspan="4" style="padding:12px; border:1px solid #CBD5E1; text-align:right;">총 합계 영업 권리 가치 (V<sub>i</sub>)</td>'
            '            <td style="padding:12px; border:1px solid #CBD5E1; color:#4F46E5; font-size:1.1rem;">7,460만 원</td>'
            '        </tr>'
            '    </tbody>'
            '</table>'
            '<h4 style="color:#0D9488; margin: 20px 0 10px 0;">⚖️ 감정평가 공식 vs 일반 시장 관행의 차이</h4>'
            '<ul style="padding-left: 20px; line-height: 1.8;">'
            '    <li><strong>공식 감정평가 (수익환원법):</strong> 소송, 법적 분쟁 시 상가건물임대차보호법에 규정된 손해배상액을 산정할 때는 법원 지침에 따라 이 수익환원법을 사용하여 과학적으로 계산합니다.</li>'
            '    <li><strong>현업 중개 관행 (승수 방식):</strong> 실제 부동산 시장에서는 공식 수식을 계산하기 번거로우므로, 약식으로 <strong>\'평균 순영업이익의 6개월 ~ 12개월분\'</strong>을 권리금(호가)으로 상정하여 거래하는 간편 계산 관행이 통용됩니다.</li>'
            '</ul>'
        )
    elif best_doc_id == 6:
        answer = (
            '<h3 style="margin-top:0; color:#4F46E5; font-family:\'Outfit\';">📊 공정거래위원회 정보공개서 기반 프랜차이즈 창업 검증</h3>'
            '<p>가맹 브랜드 양수 시, 가맹본사의 홍보 자료에만 의존하지 않고 공정위 공식 정보공개서 데이터를 기반으로 교차 검증해야 안정성을 담보할 수 있습니다.</p>'
            '<h4 style="color:#0D9488; margin: 15px 0 8px 0;">📑 핵심 비교 검증 3대 지표</h4>'
            '<ul style="padding-left: 20px; line-height: 1.8;">'
            '    <li><strong>가맹점 평균 매출액 대조:</strong> 가맹본부가 주장하는 매출액과 공정위에 공시된 <em>지역별 연간 평균 매출액</em>을 반드시 비교 대조하여 실질 수익성을 파악하십시오.</li>'
            '    <li><strong>창업 초기 총비용 산출:</strong> 가맹비, 교육비, 보증금뿐만 아니라 본사 지정 평당 인테리어 비용 등 실제 지불해야 할 필수 고정 자본금을 확인하십시오.</li>'
            '    <li><strong>가맹점 개폐업율 추이 분석:</strong> 신규 개점 수 대비 폐점(계약종료/해지) 비중을 분석하여 브랜드의 시장 안정성과 수명을 진단하십시오.</li>'
            '</ul>'
            '<p style="font-size:0.9rem; color:#475569;">※ 저희 플랫폼의 \'실시간 정보공개서 비교 툴\'을 통해 각 프랜차이즈 본사별로 공시한 재무건전성 및 매출 수치를 다차원 시각화 그래프로 즉시 비교할 수 있습니다.</p>'
        )
    else:
        answer = (
            '<h3 style="margin-top:0; color:#4F46E5; font-family:\'Outfit\';">💳 에스크로 안전 결제 및 거래 수수료 자동 정산 안내</h3>'
            '<p>점포 거래 시 계약금의 횡령 및 먹튀 사기를 미연에 차단하고 원활한 잔금 인계 과정을 보장하기 위해 <strong>에스크로(안심 거래) 안전 계좌</strong> 연동 서비스를 적용합니다.</p>'
            '<h4 style="color:#0D9488; margin: 15px 0 8px 0;">🔄 에스크로 정산 안전 프로세스</h4>'
            '<ol style="padding-left: 20px; line-height: 1.8;">'
            '    <li><strong>안심 계좌 예치:</strong> 계약금 및 권리금이 매도자 계좌로 바로 입금되지 않고 제3의 안전 예치 계좌(에스크로)에 보존됩니다.</li>'
            '    <li><strong>행정 및 영업 이전 검증:</strong> 실제 건물 임대차 계약 체결, 신규 인허가 양도 절차, 국세청 사업자등록 폐업 및 신규 개업이 정상적으로 종료되었는지 시스템 및 서면으로 실시간 대조 확인합니다.</li>'
            '    <li><strong>매도인 자동 잔금 송금:</strong> 이전 절차가 완전히 완료되면 에스크로 안전 계좌에 묶여있던 자금이 매도인의 정산 계좌로 자동 해제되어 송금됩니다.</li>'
            '    <li><strong>중개 수수료 정산:</strong> 양 당사자가 합의한 권리 양도양수 법정 수수료(평가 총액의 3%~5% 범위 내 협의)도 이체 시점에 투명하게 선 정산 처리됩니다.</li>'
            '</ol>'
        )
        
    return answer, sources

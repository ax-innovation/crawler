"""
정부지원 금융상품 수집 모듈
- 청년도약계좌, 디딤돌대출, 버팀목전세자금 등 정적 데이터
- 서민금융진흥원 API (data.go.kr 키 있을 때만 실행)
"""

import requests
import time
from dataclasses import dataclass, field
from typing import Optional
from xml.etree import ElementTree as ET


@dataclass
class GovProduct:
    product_id: str
    source: str
    category: str
    product_name: str
    institution: str
    target: str
    age_min: Optional[int]
    age_max: Optional[int]
    income_limit: Optional[str]
    rate_info: str
    limit_amount: Optional[str]
    period: Optional[str]
    benefit: str
    apply_url: str
    extra: dict = field(default_factory=dict)


# ── 서민금융진흥원 API ────────────────────────────────────────

class KinfaCollector:
    BASE = "http://apis.data.go.kr/B553701"

    def __init__(self, service_key: str, delay: float = 0.3):
        self.service_key = service_key
        self.delay = delay
        self.session = requests.Session()

    def _get_xml(self, endpoint: str, params: dict) -> ET.Element:
        params["serviceKey"] = self.service_key
        params.setdefault("numOfRows", "100")
        params.setdefault("pageNo", "1")
        resp = self.session.get(f"{self.BASE}/{endpoint}", params=params, timeout=10)
        resp.raise_for_status()
        return ET.fromstring(resp.content)

    def _fetch_all(self, endpoint: str) -> list[dict]:
        all_items = []
        page = 1
        while True:
            root = self._get_xml(endpoint, {"pageNo": str(page)})
            body = root.find(".//body")
            if body is None:
                break
            items = body.findall(".//item")
            if not items:
                break
            for item in items:
                row = {child.tag: (child.text or "").strip() for child in item}
                all_items.append(row)
            total_count = int(root.findtext(".//totalCount") or "0")
            num_of_rows = int(root.findtext(".//numOfRows") or "100")
            if page * num_of_rows >= total_count:
                break
            page += 1
            time.sleep(self.delay)
        print(f"  └─ [{endpoint}] 총 {len(all_items)}개 수집")
        return all_items

    def fetch_loan_products(self) -> list[GovProduct]:
        print("[서민금융진흥원] 대출상품 수집 시작")
        raw = self._fetch_all("LoanProductsInfoService/getLoanProductInfo")
        return [GovProduct(
            product_id=f"kinfa_loan_{r.get('prdtNo', '')}",
            source="kinfa", category="서민대출",
            product_name=r.get("prdtNm", ""),
            institution=r.get("hndlInstNm", ""),
            target=r.get("trtSmryTxn", ""),
            age_min=None, age_max=None,
            income_limit=r.get("incmCndTxn", ""),
            rate_info=r.get("lndRateTxn", ""),
            limit_amount=r.get("lndLmtTxn", ""),
            period=r.get("lndTrmTxn", ""),
            benefit=r.get("etcCndTxn", ""),
            apply_url="https://www.kinfa.or.kr",
            extra=r,
        ) for r in raw]

    def fetch_saving_products(self) -> list[GovProduct]:
        print("[서민금융진흥원] 자산형성상품 수집 시작")
        raw = self._fetch_all("SvingProductsInfoService/getSvingProductInfo")
        return [GovProduct(
            product_id=f"kinfa_sav_{r.get('prdtNo', '')}",
            source="kinfa", category="자산형성",
            product_name=r.get("prdtNm", ""),
            institution=r.get("hndlInstNm", ""),
            target=r.get("trtSmryTxn", ""),
            age_min=None, age_max=None,
            income_limit=r.get("incmCndTxn", ""),
            rate_info=r.get("svngRateTxn", ""),
            limit_amount=r.get("svngLmtTxn", ""),
            period=r.get("svngTrmTxn", ""),
            benefit=r.get("benefitTxn", ""),
            apply_url="https://ylaccount.kinfa.or.kr",
            extra=r,
        ) for r in raw]


# ── 청년도약계좌 정적 데이터 ──────────────────────────────────

YOUTH_LEAP_ACCOUNT = GovProduct(
    product_id="static_youth_leap_account",
    source="static", category="자산형성",
    product_name="청년도약계좌",
    institution="서민금융진흥원 (취급: 11개 은행)",
    target="만 19~34세 / 총급여 7,500만원 이하 / 가구소득 중위 250% 이하",
    age_min=19, age_max=34,
    income_limit="총급여 7,500만원 이하",
    rate_info="은행별 기본금리 + 우대금리",
    limit_amount="월 최대 70만원 × 60개월",
    period="60개월 (5년)",
    benefit="정부기여금 월 최대 6% / 이자소득 비과세",
    apply_url="https://ylaccount.kinfa.or.kr",
    extra={
        "gov_contribution": {
            "총급여_2400만원이하": {"기여금비율": "6.0%", "월최대": "24,000원"},
            "총급여_3600만원이하": {"기여금비율": "4.6%", "월최대": "23,000원"},
            "총급여_4800만원이하": {"기여금비율": "3.7%", "월최대": "22,000원"},
            "총급여_6000만원이하": {"기여금비율": "3.0%", "월최대": "21,000원"},
            "총급여_7500만원이하": {"기여금비율": "없음",  "월최대": "0원"},
        },
        "rates_by_bank": {              # ← 추가
            "국민은행":  {"base": 4.5, "best": 6.0},
            "농협은행":  {"base": 4.5, "best": 6.0},
            "신한은행":  {"base": 4.5, "best": 6.0},
            "우리은행":  {"base": 4.5, "best": 6.0},
            "하나은행":  {"base": 4.5, "best": 6.0},
            "기업은행":  {"base": 4.5, "best": 6.0},
            "부산은행":  {"base": 4.5, "best": 6.0},
            "광주은행":  {"base": 4.5, "best": 6.0},
            "전북은행":  {"base": 4.5, "best": 6.0},
            "경남은행":  {"base": 4.5, "best": 6.0},
            "대구은행":  {"base": 4.5, "best": 6.0},
        },
        "eligible_banks": [
            "국민은행", "농협은행", "신한은행", "우리은행", "하나은행",
            "기업은행", "부산은행", "광주은행", "전북은행", "경남은행", "대구은행"
        ],
    },
)

# ── 주택도시기금 정책대출 정적 데이터 ────────────────────────

HOUSING_FUND_PRODUCTS = [
    GovProduct(
        product_id="static_didimdol",
        source="static", category="정책대출",
        product_name="내집마련 디딤돌대출",
        institution="주택도시기금 (취급: 국민·농협·신한·우리·하나·부산·iM뱅크)",
        target="무주택 세대주 / 부부합산 연소득 6,000만원 이하",
        age_min=None, age_max=None,
        income_limit="부부합산 연소득 6,000만원 이하 (생애최초·신혼 7,000만원)",
        rate_info="연 2.15%~3.00%",
        limit_amount="최대 4억원 (LTV 70% 이내)",
        period="10·15·20·30년",
        benefit="생애최초 0.1%p 추가 우대 / 신혼·다자녀 우대",
        apply_url="https://enhuf.molit.go.kr",
        extra={},
    ),
    GovProduct(
        product_id="static_butimok",
        source="static", category="정책대출",
        product_name="버팀목전세자금",
        institution="주택도시기금 (취급: 국민·농협·신한·우리·하나·부산·iM뱅크)",
        target="무주택 세대주 / 부부합산 연소득 5,000만원 이하",
        age_min=None, age_max=None,
        income_limit="부부합산 연소득 5,000만원 이하 (신혼 6,000만원)",
        rate_info="연 2.1%~2.9%",
        limit_amount="수도권 1.2억원 / 지방 8,000만원",
        period="2년 (4회 연장, 최장 10년)",
        benefit="신혼 0.2%p 우대 / 다자녀 추가 우대",
        apply_url="https://enhuf.molit.go.kr",
        extra={},
    ),
    GovProduct(
        product_id="static_youth_butimok",
        source="static", category="정책대출",
        product_name="청년전용 버팀목전세자금",
        institution="주택도시기금 (취급: 국민·농협·신한·우리·하나·부산·iM뱅크)",
        target="만 19~34세 단독세대주 / 연소득 5,000만원 이하",
        age_min=19, age_max=34,
        income_limit="연소득 5,000만원 이하 / 순자산 3.61억원 이하",
        rate_info="연 1.5%~2.1%",
        limit_amount="최대 2,000만원",
        period="2년 (4회 연장, 최장 10년)",
        benefit="일반 버팀목 대비 0.5~0.6%p 낮은 우대금리",
        apply_url="https://enhuf.molit.go.kr",
        extra={},
    ),
]

# ── 서민금융 정적 폴백 ────────────────────────────────────────

def _static_kinfa_products() -> list[GovProduct]:
    return [
        GovProduct(
            product_id="static_haessal_15", source="static", category="서민대출",
            product_name="햇살론15",
            institution="서민금융진흥원 (취급: 저축은행·상호금융)",
            target="연소득 3,500만원 이하 또는 신용점수 하위 20%",
            age_min=None, age_max=None,
            income_limit="연소득 3,500만원 이하 또는 신용점수 하위 20%",
            rate_info="연 최대 15.9%", limit_amount="최대 700만원", period="최장 5년",
            benefit="중금리 대출 / 보증서 발급", apply_url="https://www.kinfa.or.kr", extra={},
        ),
        GovProduct(
            product_id="static_haessal_youth", source="static", category="서민대출",
            product_name="햇살론유스",
            institution="서민금융진흥원 (취급: 저축은행·신협 등)",
            target="만 19~34세 / 연소득 3,500만원 이하 또는 신용점수 하위 20%",
            age_min=19, age_max=34,
            income_limit="연소득 3,500만원 이하 또는 신용점수 하위 20%",
            rate_info="연 최대 12.0%", limit_amount="최대 1,200만원", period="최장 5년",
            benefit="청년 특화 저금리 / 취업·창업 지원 연계",
            apply_url="https://www.kinfa.or.kr", extra={},
        ),
    ]


# ── 통합 수집기 ──────────────────────────────────────────────

class GovProductCollector:
    def __init__(self, data_go_key: Optional[str] = None):
        self.kinfa = KinfaCollector(data_go_key) if data_go_key else None

    def fetch_all(self) -> dict[str, list[GovProduct]]:
        result = {
            "서민대출": [],
            "자산형성": [YOUTH_LEAP_ACCOUNT],
            "정책대출": HOUSING_FUND_PRODUCTS[:],
        }
        if self.kinfa:
            try:
                result["서민대출"] += self.kinfa.fetch_loan_products()
            except Exception as e:
                print(f"  ⚠️  서민대출 API 오류: {e} → 정적 데이터 사용")
                result["서민대출"] += _static_kinfa_products()
            try:
                result["자산형성"] += self.kinfa.fetch_saving_products()
            except Exception as e:
                print(f"  ⚠️  자산형성 API 오류: {e}")
        else:
            print("⚠️  DATA_GO_KEY 미설정 → 정적 데이터 사용")
            result["서민대출"] += _static_kinfa_products()
        return result

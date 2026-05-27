"""
금융감독원 금융상품한눈에 API 데이터 수집 모듈
API 키 발급: https://finlife.fss.or.kr → 오픈API → 인증키 신청
"""

import requests
import time
from dataclasses import dataclass, field
from typing import Optional

BASE_URL = "http://finlife.fss.or.kr/finlifeapi"

ENDPOINTS = {
    "정기예금":     "depositProductsSearch",
    "적금":         "savingProductsSearch",
    "주택담보대출": "mortgageLoanProductsSearch",
    "전세자금대출": "rentHouseLoanProductsSearch",
    "개인신용대출": "creditLoanProductsSearch",
}


@dataclass
class DepositProduct:
    fin_prdt_cd: str
    kor_co_nm: str
    fin_prdt_nm: str
    join_way: str
    mtrt_int: str
    spcl_cnd: str
    join_deny: str
    join_member: str
    etc_note: str
    max_limit: Optional[float]
    dcls_strt_day: str
    fin_co_no: str
    options: list = field(default_factory=list)


@dataclass
class DepositOption:
    fin_prdt_cd: str
    intr_rate_type: str
    intr_rate_type_nm: str
    save_trm: str
    intr_rate: float
    intr_rate2: float


@dataclass
class LoanProduct:
    fin_prdt_cd: str
    kor_co_nm: str
    fin_prdt_nm: str
    join_way: str
    loan_inci_expn: str
    erly_rpay_fee: str
    dly_rate: str
    loan_lmt: str
    dcls_strt_day: str
    fin_co_no: str
    options: list = field(default_factory=list)


@dataclass
class LoanOption:
    fin_prdt_cd: str
    mrtg_type: str
    mrtg_type_nm: str
    rpay_type: str
    rpay_type_nm: str
    lend_rate_type: str
    lend_rate_type_nm: str
    lend_rate_min: float
    lend_rate_max: float
    lend_rate_avg: Optional[float]


class FinlifeCollector:
    def __init__(self, api_key: str, delay: float = 0.5):
        self.api_key = api_key
        self.delay = delay
        self.session = requests.Session()
        self.session.headers.update({"Accept": "application/json"})

    def _get(self, endpoint: str, top_fin_grp_no: str, page_no: int = 1) -> dict:
        url = f"{BASE_URL}/{endpoint}.json"
        params = {"auth": self.api_key, "topFinGrpNo": top_fin_grp_no, "pageNo": page_no}
        resp = self.session.get(url, params=params, timeout=40)
        resp.raise_for_status()
        return resp.json()

    def _fetch_all_pages(self, endpoint: str, top_fin_grp_no: str):
        all_base, all_opts = [], []
        page = 1
        while True:
            data = self._get(endpoint, top_fin_grp_no, page)
            result = data.get("result", {})
            all_base.extend(result.get("baseList", []))
            all_opts.extend(result.get("optionList", []))
            max_page_no = int(result.get("max_page_no", 1))
            total_count = int(result.get("total_count", 0))
            print(f"  └─ [{endpoint}] 페이지 {page}/{max_page_no} | 누적 {len(all_base)}/{total_count}개")
            if page >= max_page_no:
                break
            page += 1
            time.sleep(self.delay)
        return all_base, all_opts

    def _parse_deposit_products(self, base_list, opt_list):
        opts_by_code = {}
        for o in opt_list:
            code = o.get("fin_prdt_cd", "")
            opts_by_code.setdefault(code, []).append(
                DepositOption(
                    fin_prdt_cd=code,
                    intr_rate_type=o.get("intr_rate_type", ""),
                    intr_rate_type_nm=o.get("intr_rate_type_nm", ""),
                    save_trm=o.get("save_trm", ""),
                    intr_rate=float(o.get("intr_rate") or 0),
                    intr_rate2=float(o.get("intr_rate2") or 0),
                )
            )
        products = []
        for b in base_list:
            code = b.get("fin_prdt_cd", "")
            products.append(DepositProduct(
                fin_prdt_cd=code,
                kor_co_nm=b.get("kor_co_nm", ""),
                fin_prdt_nm=b.get("fin_prdt_nm", ""),
                join_way=b.get("join_way", ""),
                mtrt_int=b.get("mtrt_int", ""),
                spcl_cnd=b.get("spcl_cnd", ""),
                join_deny=b.get("join_deny", ""),
                join_member=b.get("join_member", ""),
                etc_note=b.get("etc_note", ""),
                max_limit=float(b["max_limit"]) if b.get("max_limit") else None,
                dcls_strt_day=b.get("dcls_strt_day", ""),
                fin_co_no=b.get("fin_co_no", ""),
                options=opts_by_code.get(code, []),
            ))
        return products

    def _parse_loan_products(self, base_list, opt_list):
        opts_by_code = {}
        for o in opt_list:
            code = o.get("fin_prdt_cd", "")
            opts_by_code.setdefault(code, []).append(
                LoanOption(
                    fin_prdt_cd=code,
                    mrtg_type=o.get("mrtg_type", ""),
                    mrtg_type_nm=o.get("mrtg_type_nm", ""),
                    rpay_type=o.get("rpay_type", ""),
                    rpay_type_nm=o.get("rpay_type_nm", ""),
                    lend_rate_type=o.get("lend_rate_type", ""),
                    lend_rate_type_nm=o.get("lend_rate_type_nm", ""),
                    lend_rate_min=float(o.get("lend_rate_min") or 0),
                    lend_rate_max=float(o.get("lend_rate_max") or 0),
                    lend_rate_avg=float(o["lend_rate_avg"]) if o.get("lend_rate_avg") else None,
                )
            )
        products = []
        for b in base_list:
            code = b.get("fin_prdt_cd", "")
            products.append(LoanProduct(
                fin_prdt_cd=code,
                kor_co_nm=b.get("kor_co_nm", ""),
                fin_prdt_nm=b.get("fin_prdt_nm", ""),
                join_way=b.get("join_way", ""),
                loan_inci_expn=b.get("loan_inci_expn", ""),
                erly_rpay_fee=b.get("erly_rpay_fee", ""),
                dly_rate=b.get("dly_rate", ""),
                loan_lmt=b.get("loan_lmt", ""),
                dcls_strt_day=b.get("dcls_strt_day", ""),
                fin_co_no=b.get("fin_co_no", ""),
                options=opts_by_code.get(code, []),
            ))
        return products

    def fetch_deposits(self, fin_grp_no: str = "020000"):
        print("[정기예금] 수집 시작")
        base, opts = self._fetch_all_pages(ENDPOINTS["정기예금"], fin_grp_no)
        return self._parse_deposit_products(base, opts)

    def fetch_savings(self, fin_grp_no: str = "020000"):
        print("[적금] 수집 시작")
        base, opts = self._fetch_all_pages(ENDPOINTS["적금"], fin_grp_no)
        return self._parse_deposit_products(base, opts)

    def fetch_mortgage_loans(self, fin_grp_no: str = "020000"):
        print("[주택담보대출] 수집 시작")
        base, opts = self._fetch_all_pages(ENDPOINTS["주택담보대출"], fin_grp_no)
        return self._parse_loan_products(base, opts)

    def fetch_rent_loans(self, fin_grp_no: str = "020000"):
        print("[전세자금대출] 수집 시작")
        base, opts = self._fetch_all_pages(ENDPOINTS["전세자금대출"], fin_grp_no)
        return self._parse_loan_products(base, opts)

    def fetch_credit_loans(self, fin_grp_no: str = "020000"):
        print("[개인신용대출] 수집 시작")
        base, opts = self._fetch_all_pages(ENDPOINTS["개인신용대출"], fin_grp_no)
        return self._parse_loan_products(base, opts)

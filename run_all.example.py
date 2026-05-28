"""
금융상품 데이터 통합 수집 + DB 저장 스크립트

★ 실행 전 아래 값들을 본인 환경에 맞게 수정하세요 ★
"""

import os
from datetime import datetime

from collector import FinlifeCollector
from gov_collector import GovProductCollector
from db_writer import DBWriter


def run():
    # ──────────────────────────────────────────────────────
    # ★ 여기를 수정하세요
    # ──────────────────────────────────────────────────────
    finlife_key = "여기에_금감원_API키_입력"       # finlife.fss.or.kr 에서 발급
    data_go_key = ""                               # data.go.kr 키 (없으면 빈 문자열)
    db_host     = "localhost"
    db_user     = "root"
    db_pass     = "여기에_MySQL_비밀번호_입력"
    db_name     = "findb"
    db_port     = 3306
    # ──────────────────────────────────────────────────────

    print("=" * 60)
    print("  금융상품 통합 수집기")
    print(f"  실행 시각: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    writer = DBWriter(host=db_host, user=db_user, password=db_pass,
                      db=db_name, port=db_port)
    writer.setup()

    summary = {}

    # ── ① 금감원 API 수집 ───────────────────────────────────
    if finlife_key and finlife_key != "여기에_금감원_API키_입력":
        print("\n[1/2] 금융감독원 금융상품한눈에 API 수집")
        fc = FinlifeCollector(api_key=finlife_key, delay=0.5)

        deposits = fc.fetch_deposits()
        savings  = fc.fetch_savings()
        writer.upsert_deposits(deposits)
        writer.upsert_savings(savings)
        summary["금감원_정기예금"] = len(deposits)
        summary["금감원_적금"]     = len(savings)

        mortgage = fc.fetch_mortgage_loans()
        rent     = fc.fetch_rent_loans()
        credit   = fc.fetch_credit_loans()
        writer.upsert_mortgage_loans(mortgage)
        writer.upsert_rent_loans(rent)
        writer.upsert_credit_loans(credit)
        summary["금감원_주택담보대출"] = len(mortgage)
        summary["금감원_전세자금대출"] = len(rent)
        summary["금감원_개인신용대출"] = len(credit)
    else:
        print("\n[1/2] ⚠️  FINLIFE_API_KEY 미설정 → 금감원 수집 건너뜀")

    # ── ② 정부지원 상품 수집 ────────────────────────────────
    print("\n[2/2] 정부지원 금융상품 수집")
    gc = GovProductCollector(data_go_key=data_go_key if data_go_key else None)
    gov_data = gc.fetch_all()
    for category, products in gov_data.items():
        writer.upsert_gov_products(products)
        summary[f"정부지원_{category}"] = len(products)

    # ── 결과 요약 ─────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("  수집 완료 요약")
    print("=" * 60)
    total = 0
    for label, count in summary.items():
        print(f"  {label:25} {count:4}개")
        total += count
    print(f"  {'합계':25} {total:4}개")
    print(f"\n  완료 시각: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    run()

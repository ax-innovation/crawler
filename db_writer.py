"""
MySQL upsert 저장 모듈
설치: pip install pymysql
"""

import pymysql
import json
from dataclasses import asdict

DDL = """
CREATE TABLE IF NOT EXISTS finance_product (
    id              BIGINT AUTO_INCREMENT PRIMARY KEY,
    fin_prdt_cd     VARCHAR(20)  NOT NULL,
    product_type    VARCHAR(20)  NOT NULL,
    fin_co_no       VARCHAR(20),
    kor_co_nm       VARCHAR(100),
    fin_prdt_nm     VARCHAR(200),
    join_way        VARCHAR(200),
    spcl_cnd        TEXT,
    join_member     VARCHAR(500),
    join_deny       CHAR(1),
    max_limit       BIGINT,
    dcls_strt_day   VARCHAR(8),
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uq_product (fin_prdt_cd, product_type)
) CHARACTER SET utf8mb4;

CREATE TABLE IF NOT EXISTS finance_option (
    id                  BIGINT AUTO_INCREMENT PRIMARY KEY,
    fin_prdt_cd         VARCHAR(20)  NOT NULL,
    product_type        VARCHAR(20)  NOT NULL,
    intr_rate_type      VARCHAR(5),
    intr_rate_type_nm   VARCHAR(20),
    save_trm            INT,
    intr_rate           DECIMAL(5,2),
    intr_rate2          DECIMAL(5,2),
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uq_option (fin_prdt_cd, product_type, save_trm, intr_rate_type)
) CHARACTER SET utf8mb4;

CREATE TABLE IF NOT EXISTS loan_product (
    id              BIGINT AUTO_INCREMENT PRIMARY KEY,
    fin_prdt_cd     VARCHAR(20)  NOT NULL,
    product_type    VARCHAR(20)  NOT NULL,
    fin_co_no       VARCHAR(20),
    kor_co_nm       VARCHAR(100),
    fin_prdt_nm     VARCHAR(200),
    join_way        VARCHAR(200),
    loan_inci_expn  TEXT,
    erly_rpay_fee   VARCHAR(300),
    dly_rate        VARCHAR(100),
    loan_lmt        VARCHAR(300),
    dcls_strt_day   VARCHAR(8),
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uq_loan (fin_prdt_cd, product_type)
) CHARACTER SET utf8mb4;

CREATE TABLE IF NOT EXISTS loan_option (
    id                  BIGINT AUTO_INCREMENT PRIMARY KEY,
    fin_prdt_cd         VARCHAR(20)  NOT NULL,
    product_type        VARCHAR(20)  NOT NULL,
    mrtg_type           VARCHAR(10),
    mrtg_type_nm        VARCHAR(50),
    rpay_type           VARCHAR(10),
    rpay_type_nm        VARCHAR(50),
    lend_rate_type      VARCHAR(10),
    lend_rate_type_nm   VARCHAR(50),
    lend_rate_min       DECIMAL(5,2),
    lend_rate_max       DECIMAL(5,2),
    lend_rate_avg       DECIMAL(5,2),
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uq_loan_opt (fin_prdt_cd, product_type, rpay_type, lend_rate_type)
) CHARACTER SET utf8mb4;

CREATE TABLE IF NOT EXISTS gov_product (
    id              BIGINT AUTO_INCREMENT PRIMARY KEY,
    product_id      VARCHAR(100) NOT NULL UNIQUE,
    source          VARCHAR(20),
    category        VARCHAR(30),
    product_name    VARCHAR(200),
    institution     VARCHAR(200),
    target_desc     TEXT,
    age_min         INT,
    age_max         INT,
    income_limit    VARCHAR(500),
    rate_info       VARCHAR(500),
    limit_amount    VARCHAR(200),
    period          VARCHAR(100),
    benefit         TEXT,
    apply_url       VARCHAR(300),
    extra_json      JSON,
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) CHARACTER SET utf8mb4;
"""


class DBWriter:
    def __init__(self, host: str, user: str, password: str, db: str, port: int = 3306):
        self.conn_args = dict(host=host, user=user, password=password, db=db, port=port)

    def _conn(self):
        return pymysql.connect(
            **self.conn_args, charset="utf8mb4",
            cursorclass=pymysql.cursors.DictCursor, autocommit=False,
        )

    def setup(self):
        with self._conn() as conn:
            with conn.cursor() as cur:
                for stmt in DDL.strip().split(";"):
                    stmt = stmt.strip()
                    if stmt:
                        cur.execute(stmt)
            conn.commit()
        print("✅ 테이블 준비 완료")

    # ── 예·적금 ──────────────────────────────────────────────

    def upsert_deposits(self, products: list) -> int:
        return self._upsert_fin_products(products, "정기예금")

    def upsert_savings(self, products: list) -> int:
        return self._upsert_fin_products(products, "적금")

    def _upsert_fin_products(self, products: list, product_type: str) -> int:
        if not products:
            return 0
        product_sql = """
            INSERT INTO finance_product
                (fin_prdt_cd, product_type, fin_co_no, kor_co_nm, fin_prdt_nm,
                 join_way, spcl_cnd, join_member, join_deny, max_limit, dcls_strt_day)
            VALUES (%(fin_prdt_cd)s, %(product_type)s, %(fin_co_no)s, %(kor_co_nm)s,
                    %(fin_prdt_nm)s, %(join_way)s, %(spcl_cnd)s, %(join_member)s,
                    %(join_deny)s, %(max_limit)s, %(dcls_strt_day)s)
            ON DUPLICATE KEY UPDATE
                kor_co_nm=VALUES(kor_co_nm), fin_prdt_nm=VALUES(fin_prdt_nm),
                join_way=VALUES(join_way), spcl_cnd=VALUES(spcl_cnd),
                join_member=VALUES(join_member), join_deny=VALUES(join_deny),
                max_limit=VALUES(max_limit), dcls_strt_day=VALUES(dcls_strt_day),
                updated_at=CURRENT_TIMESTAMP
        """
        option_sql = """
            INSERT INTO finance_option
                (fin_prdt_cd, product_type, intr_rate_type, intr_rate_type_nm,
                 save_trm, intr_rate, intr_rate2)
            VALUES (%(fin_prdt_cd)s, %(product_type)s, %(intr_rate_type)s,
                    %(intr_rate_type_nm)s, %(save_trm)s, %(intr_rate)s, %(intr_rate2)s)
            ON DUPLICATE KEY UPDATE
                intr_rate=VALUES(intr_rate), intr_rate2=VALUES(intr_rate2),
                updated_at=CURRENT_TIMESTAMP
        """
        count = 0
        with self._conn() as conn:
            with conn.cursor() as cur:
                for p in products:
                    d = asdict(p) if hasattr(p, "__dataclass_fields__") else p
                    options = d.pop("options", [])   # 여기도 동일하게 수정
                    d["product_type"] = product_type
                    cur.execute(product_sql, d)
                    for opt in options:
                        opt["product_type"] = product_type
                        cur.execute(option_sql, opt)
                    count += 1
            conn.commit()
        print(f"  └─ [{product_type}] {count}개 upsert 완료")
        return count

    # ── 대출 상품 ─────────────────────────────────────────────

    def upsert_mortgage_loans(self, products: list) -> int:
        return self._upsert_loan_products(products, "주택담보대출")

    def upsert_rent_loans(self, products: list) -> int:
        return self._upsert_loan_products(products, "전세자금대출")

    def upsert_credit_loans(self, products: list) -> int:
        return self._upsert_loan_products(products, "개인신용대출")

    def _upsert_loan_products(self, products: list, product_type: str) -> int:
        if not products:
            return 0
        product_sql = """
            INSERT INTO loan_product
                (fin_prdt_cd, product_type, fin_co_no, kor_co_nm, fin_prdt_nm,
                 join_way, loan_inci_expn, erly_rpay_fee, dly_rate, loan_lmt, dcls_strt_day)
            VALUES (%(fin_prdt_cd)s, %(product_type)s, %(fin_co_no)s, %(kor_co_nm)s,
                    %(fin_prdt_nm)s, %(join_way)s, %(loan_inci_expn)s, %(erly_rpay_fee)s,
                    %(dly_rate)s, %(loan_lmt)s, %(dcls_strt_day)s)
            ON DUPLICATE KEY UPDATE
                kor_co_nm=VALUES(kor_co_nm), fin_prdt_nm=VALUES(fin_prdt_nm),
                join_way=VALUES(join_way), loan_inci_expn=VALUES(loan_inci_expn),
                erly_rpay_fee=VALUES(erly_rpay_fee), dly_rate=VALUES(dly_rate),
                loan_lmt=VALUES(loan_lmt), dcls_strt_day=VALUES(dcls_strt_day),
                updated_at=CURRENT_TIMESTAMP
        """
        option_sql = """
            INSERT INTO loan_option
                (fin_prdt_cd, product_type, mrtg_type, mrtg_type_nm,
                 rpay_type, rpay_type_nm, lend_rate_type, lend_rate_type_nm,
                 lend_rate_min, lend_rate_max, lend_rate_avg)
            VALUES (%(fin_prdt_cd)s, %(product_type)s, %(mrtg_type)s, %(mrtg_type_nm)s,
                    %(rpay_type)s, %(rpay_type_nm)s, %(lend_rate_type)s, %(lend_rate_type_nm)s,
                    %(lend_rate_min)s, %(lend_rate_max)s, %(lend_rate_avg)s)
            ON DUPLICATE KEY UPDATE
                lend_rate_min=VALUES(lend_rate_min), lend_rate_max=VALUES(lend_rate_max),
                lend_rate_avg=VALUES(lend_rate_avg), updated_at=CURRENT_TIMESTAMP
        """
        count = 0
        with self._conn() as conn:
            with conn.cursor() as cur:
                for p in products:
                    d = asdict(p) if hasattr(p, "__dataclass_fields__") else p
                    options = d.pop("options", [])   # ← 이 줄 추가
                    d["product_type"] = product_type
                    cur.execute(product_sql, d)
                    for opt in options:
                        opt["product_type"] = product_type
                        cur.execute(option_sql, opt)
                    count += 1
            conn.commit()
        print(f"  └─ [{product_type}] {count}개 upsert 완료")
        return count

    # ── 정부지원 상품 ─────────────────────────────────────────

    def upsert_gov_products(self, products: list) -> int:
        if not products:
            return 0
        sql = """
            INSERT INTO gov_product
                (product_id, source, category, product_name, institution,
                 target_desc, age_min, age_max, income_limit, rate_info,
                 limit_amount, period, benefit, apply_url, extra_json)
            VALUES (%(product_id)s, %(source)s, %(category)s, %(product_name)s,
                    %(institution)s, %(target_desc)s, %(age_min)s, %(age_max)s,
                    %(income_limit)s, %(rate_info)s, %(limit_amount)s, %(period)s,
                    %(benefit)s, %(apply_url)s, %(extra_json)s)
            ON DUPLICATE KEY UPDATE
                product_name=VALUES(product_name), institution=VALUES(institution),
                target_desc=VALUES(target_desc), age_min=VALUES(age_min),
                age_max=VALUES(age_max), income_limit=VALUES(income_limit),
                rate_info=VALUES(rate_info), limit_amount=VALUES(limit_amount),
                period=VALUES(period), benefit=VALUES(benefit),
                apply_url=VALUES(apply_url), extra_json=VALUES(extra_json),
                updated_at=CURRENT_TIMESTAMP
        """
        count = 0
        with self._conn() as conn:
            with conn.cursor() as cur:
                for p in products:
                    d = asdict(p) if hasattr(p, "__dataclass_fields__") else p
                    d["target_desc"] = d.pop("target", "")
                    d["extra_json"]  = json.dumps(d.pop("extra", {}), ensure_ascii=False)
                    cur.execute(sql, d)
                    count += 1
            conn.commit()
        print(f"  └─ [정부지원상품] {count}개 upsert 완료")
        return count

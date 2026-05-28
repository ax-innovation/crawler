# 금융상품 데이터 수집기

금융감독원 API와 공공데이터포털 API를 활용해 금융상품 데이터를 수집하고 MySQL에 저장하는 Python 수집기입니다.

## 기술 스택
- Python 3.11+
- requests (HTTP 요청)
- pymysql (MySQL 연동)

## 수집 데이터
| 데이터 | 출처 | 방식 |
|---|---|---|
| 정기예금 | 금융감독원 finlife API | 자동 수집 |
| 적금 | 금융감독원 finlife API | 자동 수집 |
| 주택담보대출 | 금융감독원 finlife API | 자동 수집 |
| 전세자금대출 | 금융감독원 finlife API | 자동 수집 |
| 개인신용대출 | 금융감독원 finlife API | 자동 수집 |
| 청년도약계좌 | 없음 (정적 데이터) | 코드 내 관리 |
| 디딤돌대출 | 없음 (정적 데이터) | 코드 내 관리 |
| 버팀목전세자금 | 없음 (정적 데이터) | 코드 내 관리 |

## 실행 전 준비

### 1. API 키 발급
| API | 발급처 |
|---|---|
| 금감원 API | https://finlife.fss.or.kr → 오픈API → 인증키 신청 |
| 공공데이터포털 | https://www.data.go.kr → 회원가입 후 신청 |

### 2. MySQL DB 생성
```sql
mysql -u root -p
CREATE DATABASE findb CHARACTER SET utf8mb4;
```

## 실행 방법

### 1. 저장소 받아오기
```bash
git clone https://github.com/ax-innovation/crawler.git
cd crawler
```

### 2. 라이브러리 설치
```bash
pip install requests pymysql
```

### 3. 설정 파일 생성
```bash
cp run_all.example.py run_all.py
```
`run_all.py` 열어서 아래 항목 입력:
```python
finlife_key = "발급받은_금감원_API키"
data_go_key = ""               # 없으면 빈 문자열
db_host     = "localhost"
db_user     = "root"
db_pass     = "MySQL_비밀번호"
db_name     = "findb"
db_port     = 3306
```

### 4. 실행
```bash
python run_all.py
```

## DB 테이블 구조
| 테이블 | 설명 |
|---|---|
| finance_product | 예·적금 상품 기본정보 |
| finance_option | 예·적금 기간별 금리 |
| loan_product | 대출 상품 기본정보 |
| loan_option | 대출 금리 옵션 |
| gov_product | 정부지원 상품 |

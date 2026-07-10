# 잡코리아 채용공고 크롤러 (crawl.py)

잡코리아(jobkorea.co.kr)에서 키워드로 채용공고를 검색해 수집하고, 엑셀 파일로 저장하는 파이썬 스크립트입니다.

## 기능

- Playwright로 잡코리아 검색 페이지를 렌더링해서 크롤링
- 원하는 키워드 / 페이지 범위(start_page ~ end_page) 지정 가능
- 수집한 데이터를 정제해서 `잡코리아_DB적재용_리스트.xlsx` 파일로 저장
- MariaDB 저장 기능은 현재 주석 처리되어 있음 (DB 미설치 환경 대응)

## 요구 사항

Python 3.9 이상 권장.

```
pip install playwright beautifulsoup4 pandas openpyxl
playwright install chromium
```

## 사용 방법

1. `crawl.py` 하단 `main()` 함수에서 검색 조건을 원하는 값으로 수정합니다.

```python
keyword = "파이썬 개발자"   # 검색 키워드
start_page = 1              # 크롤링 시작 페이지
end_page = 5                 # 크롤링 종료 페이지
```

2. 스크립트를 실행합니다.

```
python crawl.py
```

3. 실행이 끝나면 스크립트를 실행한 위치(현재 작업 디렉토리)에 `잡코리아_DB적재용_리스트.xlsx` 파일이 생성됩니다.

## 주의 사항

- 결과 엑셀 파일이 이미 다른 프로그램(엑셀 등)에서 열려 있으면 `PermissionError`가 발생합니다. 실행 전 닫아주세요.
- 크롤링 결과가 0건이면 잡코리아의 페이지 구조가 바뀌었을 가능성이 있습니다. 이 경우 스크립트가 자동으로 `debug_page_N.html` 파일을 저장하니, 이 파일을 열어 실제 HTML 구조를 확인하고 선택자(selector)를 다시 맞춰야 합니다.
- 현재 선택자는 2026년 리뉴얼된 잡코리아 구조(`data-sentry-component` 속성 기반)에 맞춰져 있습니다. 사이트가 다시 개편되면 선택자도 함께 업데이트해야 합니다.
- 목록 화면에는 학력(`edu_require`)·고용형태(`emp_type`) 정보가 더 이상 표시되지 않아 해당 컬럼은 빈 값으로 저장됩니다. 필요하다면 상세 페이지까지 들어가서 별도로 가져와야 합니다.
- MariaDB 저장 기능(`setup_database`, `save_to_mariadb`)은 주석 처리되어 있습니다. DB를 설치한 뒤 `DB_CONFIG` 값을 채우고 주석을 해제하면 사용할 수 있습니다.

## 출력 컬럼

| 컬럼명 | 설명 |
|---|---|
| source | 출처 (고정값: 잡코리아) |
| platform_post_id | 공고 고유 ID |
| job_part | 검색 키워드 |
| company_name | 회사명 |
| post_title | 공고 제목 |
| region | 근무 지역 |
| personal_history | 경력 조건 |
| edu_require | 학력 조건 (현재 미수집) |
| emp_type | 고용 형태 (현재 미수집) |
| pay | 급여 |
| end_at | 마감일 |
| crawled_at | 수집 시각 |
| job_url | 공고 상세 URL |

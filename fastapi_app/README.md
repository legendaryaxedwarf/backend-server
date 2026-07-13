# FastAPI 백엔드 (인증 + 회원 + 채용공고 + 포트폴리오 + 지원 현황 API)

라즈베리파이 2B(Ubuntu 22.04) 위에서 동작하는 FastAPI 서버 코드입니다. 기능이 추가될 때마다 이 문서의 "3. API 엔드포인트"와 "6. 기능별 구현 메모"만 이어서 추가하면 되도록 구성했습니다.

## 1. 파일 구조

```
fastapi_app/
├── main.py             # FastAPI 앱 생성 + 라우터 등록
├── database.py         # MariaDB 커넥션 생성
├── security.py         # 비밀번호 해싱 + JWT 발급/검증
├── deps.py             # 인증 확인용 Depends 함수 (get_current_member)
├── auth_router.py      # 인증: signup / login / logout
├── members_router.py   # 회원: 내 정보 조회 / 희망조건 수정 / 탈퇴
├── jobs_router.py       # 채용공고: 목록 조회(+지원상태) / 지원 토글
├── portfolio_router.py  # 포트폴리오: 파일/이미지 업로드, 별칭(cname) 관리, 공개 조회
├── applications_router.py # 지원 현황: 내가 지원한 공고 목록 조회
├── requirements.txt
├── .env.example
└── README.md
```

> 새 기능 라우터를 추가할 때는 `xxx_router.py` 파일을 만들고 `main.py`에 `app.include_router(...)` 한 줄만 추가하면 됩니다.

## 2. 설치 및 설정

```
pip install -r requirements.txt
```

`.env.example`을 참고해 `.env` 파일을 만들고 값을 채웁니다.

```
DB_HOST=127.0.0.1
DB_PORT=3306
DB_USER=fastapi_app
DB_PASSWORD=실제_비밀번호
DB_NAME=apply_db
JWT_SECRET_KEY=본인이_직접_생성한_랜덤값
```

`JWT_SECRET_KEY`는 아래 명령어로 직접 생성하세요 (채팅이나 코드에 노출된 값은 절대 재사용 금지).

```
python3 -c "import secrets; print(secrets.token_hex(32))"
```

`.env`는 반드시 `.gitignore`에 등록해서 커밋되지 않도록 합니다.

## 3. 실행

```
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

`http://<서버주소>:8000/docs` (Swagger UI)에서 아래 엔드포인트를 직접 호출하며 테스트할 수 있습니다.

## 4. API 엔드포인트

새 엔드포인트를 추가할 때마다 이 표에 행만 추가하면 됩니다.

| 도메인 | Method | Path | 인증 | 설명 | 구현 파일 |
| --- | --- | --- | --- | --- | --- |
| 인증 | POST | `/api/auth/signup` | - | 회원가입 | `auth_router.py` |
| 인증 | POST | `/api/auth/login` | - | 로그인, JWT 쿠키 발급 | `auth_router.py` |
| 인증 | POST | `/api/auth/logout` | 필요 | 로그아웃, 쿠키 삭제 | `auth_router.py` |
| 회원 | GET | `/api/users/me` | 필요 | 내 정보 조회 (마이페이지) | `members_router.py` |
| 회원 | PUT | `/api/users/me/preferences` | 필요 | 희망 조건 수정 | `members_router.py` |
| 회원 | DELETE | `/api/users/me` | 필요 | 회원 탈퇴 | `members_router.py` |
| 채용공고 | GET | `/api/jobs` | 필요 | 공고 목록 조회 (job_part/region 필터, 페이지네이션, 내 지원상태 포함) | `jobs_router.py` |
| 채용공고 | PATCH | `/api/jobs/{post_id}/apply` | 필요 | 지원 여부 토글 (PENDING ↔ APPLY) | `jobs_router.py` |
| 포트폴리오 | POST | `/api/users/me/portfolio` | 필요 | 포트폴리오 이미지/파일 업로드 | `portfolio_router.py` |
| 포트폴리오 | PUT | `/api/users/me/cname` | 필요 | 별칭(cname)/포트폴리오 URL 등록·변경 | `portfolio_router.py` |
| 포트폴리오 | GET | `/api/portfolios/{cname}` | - | 별칭으로 포트폴리오 공개 조회 (외부 방문자용) | `portfolio_router.py` |
| 지원 현황 | GET | `/api/users/me/applications` | 필요 | 내가 지원한 공고 목록 조회 (상태 필터, 페이지네이션) | `applications_router.py` |

## 5. 인증 방식 설계 — 왜 JWT인가 (세션 방식과 비교)

인증 방식은 크게 "서버가 상태를 저장하는 방식(세션)"과 "서버가 아무것도 저장하지 않는 방식(JWT)"으로 나뉩니다.

**세션 방식 (서버가 DB/Redis에 저장)**
- 로그인 성공 시 서버가 세션ID를 발급하고, DB(또는 Redis)에 회원 정보를 저장. 클라이언트는 세션ID만 쿠키로 보관
- 장점: 로그아웃/강제 만료 시 서버에서 해당 행만 지우면 즉시 완전히 무효화됨. 쿠키가 탈취돼도 무의미한 랜덤값이라 정보 노출 없음
- 단점: 요청마다 DB 조회가 추가됨 (트래픽이 많을수록 부담)

**JWT 방식 (이 프로젝트가 선택)**
- 로그인 성공 시 회원 정보(`member_id`, `email`, `nickname`)와 만료시간을 담아 서명한 토큰을 발급, DB 조회 없이 서명 검증만으로 인증
- 장점: 서버 저장소가 필요 없어 구현이 단순, 서버를 여러 대로 늘려도 세션 공유 문제 없음
- 단점(트레이드오프): 로그아웃해도 토큰 자체는 만료시간(24시간) 전까지 유효함 (탈취 시 즉시 무효화 불가), payload는 서명만 되고 암호화는 안 되어 있어 민감정보 저장 금지, 서명키 유출 시 전체 토큰 위조 가능

**결정 이유**: 순수 보안 관점에서는 세션 방식이 더 안전합니다 (즉시 무효화 가능). 다만 라즈베리파이 2B(1GB RAM)에 Redis를 새로 얹는 부담, 소규모 프로젝트 규모를 고려해 서버 상태를 안 가져도 되는 JWT를 선택했고, 유효기간을 24시간으로 짧게 잡아 트레이드오프의 영향을 최소화했습니다.

## 6. 기능별 구현 메모

기능을 추가할 때마다 이 아래에 `### 기능명` 섹션을 하나씩 추가하세요.

### 인증 (auth_router.py)

- 비밀번호는 `bcrypt`로 해싱해서 저장, 로그인 시 `bcrypt.checkpw`로 비교
- 로그인 성공 시 JWT를 httpOnly 쿠키(`access_token`)로 전달, 유효기간 24시간, 알고리즘 `HS256`
- 이메일 존재 여부가 드러나지 않도록, 이메일 없음/비밀번호 틀림을 구분하지 않고 동일한 401(`INVALID_CREDENTIALS`)로 응답

### 회원 (members_router.py)

- `GET /users/me`: JWT의 `member_id`로 DB를 조회해 최신 프로필(닉네임, 희망조건, 가입일 등) 반환. 탈퇴 등으로 DB에 없으면 404
- `PUT /users/me/preferences`: 희망 직무/지역/경력/급여 수정 (`user_job_part`가 핵심 — 이후 채용공고 필터링에 사용. 학력/고용형태는 DB에 컬럼이 없어 프론트에서도 제거하기로 함)
- `DELETE /users/me`: 회원 삭제. `member_job_apply`는 FK `ON DELETE CASCADE`라 자동으로 함께 삭제되고, 응답 시 쿠키도 삭제

### 채용공고 (jobs_router.py)

- `GET /jobs`: `job` 테이블과 `member_job_apply`를 LEFT JOIN해서, 로그인한 회원의 지원 상태(`my_apply_status`)까지 한 번에 반환. `job_part`/`region`은 `LIKE '%...%'` 부분일치 필터, `page`/`size`로 페이지네이션(`LIMIT`/`OFFSET`)
- `PATCH /jobs/{post_id}/apply`: `post_id` → `job_id` 변환 후, 현재 지원 상태를 조회해 `PENDING ↔ APPLY`로 토글. `member_job_apply`에 UPSERT(`ON DUPLICATE KEY UPDATE`)로 저장하며, `APPLY`로 바뀔 때만 `applied_at`을 현재 시각으로 갱신

### 포트폴리오 (portfolio_router.py)

- 팀 회의 결정에 따라 구조화된 텍스트 필드(소개/기술스택/프로젝트 설명 등) 대신, **파일/이미지 업로드 + 별칭(cname) 링크** 방식으로 구현 (`members` 테이블에 `portfolio_img`, `portfolio_file`, `cname`, `portfolio_url` 컬럼 추가된 것 반영)
- `POST /users/me/portfolio`: 이미지/파일을 받아 nginx `WEB_ROOT` 하위(`/var/www/html/uploads/portfolio`)에 저장하고, 그 경로를 `members`에 업데이트. FastAPI 프로세스가 이 폴더에 쓰기 권한이 있어야 함 (배포 시 확인 필요)
- `PUT /users/me/cname`: `cname`은 UNIQUE라 본인 제외 중복 체크 후 저장 (중복 시 409 `CNAME_DUPLICATED`)
- `GET /portfolios/{cname}`: 로그인 불필요한 공개 엔드포인트. `member_id`, `nickname`, `portfolio_img`, `portfolio_url`만 노출 (이메일 등 비공개 정보 제외)
- `python-multipart` 패키지가 있어야 FastAPI가 파일 업로드(form-data)를 처리할 수 있음 (`requirements.txt`에 추가됨)

### 지원 현황 (applications_router.py)

- `GET /users/me/applications`: `member_job_apply`를 `job`과 INNER JOIN해서, 로그인한 회원이 지원 이력을 남긴(즉 한 번이라도 지원 토글을 한) 공고 목록을 반환. 아무 상호작용도 없는 공고는 애초에 `member_job_apply`에 행이 없어 자동으로 제외됨
- `?apply=APPLY`처럼 상태로 필터할 수 있음 (지정 안 하면 PENDING/APPLY 이력 전체 반환) — 프론트 마이페이지에서 "지원 완료만 보기" 같은 탭에 사용 가능
- `page`/`size`로 페이지네이션, 정렬은 `member_job_apply.created_at DESC` (최근 상호작용 순)
- `applied_at`/`created_at`/`end_at`은 `jobs_router.py`와 동일하게 date/datetime 객체를 문자열로 변환해서 반환

## 7. 다음 단계

인증/회원/채용공고/포트폴리오/지원 현황 API까지 구현 완료. 관리자 크롤링 트리거 API(`POST /jobs/crawl`)는 팀 결정으로 진행하지 않기로 함 — 크롤링은 기존대로 `crawl3.py` + crontab 자동 실행만 사용.

남은 건 API 구현이 아니라 배포/운영 작업입니다: FastAPI systemd 서비스 등록, 업로드 폴더(`/var/www/html/uploads/portfolio`) 쓰기 권한 확인, 실제 라즈베리파이 MariaDB 대상 라이브 테스트, 프론트엔드 실제 연동. 새 API 기능이 추가되면 4번 표와 6번 메모에 이어서 추가해주세요.

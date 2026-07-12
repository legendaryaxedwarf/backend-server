# Discord Job Notifier Bot

리눅스 서버의 MySQL DB에 저장된 채용 공고(`job` 테이블)를 조회하여,
매일 지정한 시간에 특정 직무(job_part) 신규 공고를 디스코드 채널로 알림 보내는 봇입니다.

## 대상 환경

- Ubuntu 22.04
- Python 3
- MySQL

## 프로젝트 구조

```
job_notifier/
├── .env                    # 실제 설정값 (직접 생성, .env.example 참고)
├── .env.example            # 설정 템플릿
├── config.py               # 환경변수 로딩
├── db.py                   # DB 조회
├── bot.py                  # 디스코드 봇 + 스케줄러
├── job-notifier.service    # systemd 서비스 등록 파일
├── requirements.txt
└── README.md
```

## DB 테이블 (job)

| 컬럼 | 설명 |
|------|------|
| job_id | PK, auto_increment |
| source | 플랫폼 [SARAMIN, JOBKOREA] |
| job_part | 직무 |
| company_name | 회사명 |
| post_title | 공고제목 |
| region | 지역 |
| personal_history | 경력조건 |
| pay | 급여 |
| end_at | 마감일 |
| crawled_at | 크롤링 날짜 |
| job_url | 링크 |
| post_id | 고유번호 UNIQUE (같은 공고 제거) |
| apply | 지원여부 [PENDING, APPLY] |

## 설치

```bash
cd ~/job_notifier

# 가상환경 생성 및 활성화
python3 -m venv venv
source venv/bin/activate

# 의존성 설치
pip install -r requirements.txt
```

## 설정

`.env.example`을 복사해 `.env`를 만들고 값을 채웁니다.

```bash
cp .env.example .env
nano .env
```

| 변수 | 설명 |
|------|------|
| DISCORD_TOKEN | 디스코드 봇 토큰 |
| CHANNEL_ID | 알림을 보낼 채널 ID |
| DB_HOST / DB_PORT / DB_USER / DB_PASSWORD / DB_NAME | MySQL 접속 정보 |
| NOTIFY_HOUR / NOTIFY_MINUTE | 알림 시각 (24시간 형식, Asia/Seoul) |
| TARGET_JOB_PARTS | 알림 대상 직무 (쉼표 구분, 비우면 전체) |

## 디스코드 봇 준비

1. https://discord.com/developers/applications 에서 애플리케이션 생성
2. **Bot** 탭에서 봇 생성 후 TOKEN 복사 → `.env`의 `DISCORD_TOKEN`
3. **OAuth2 → URL Generator**에서 `bot` 스코프, `Send Messages` + `Embed Links` 권한 선택 후 생성된 URL로 서버 초대
4. 디스코드 설정에서 개발자 모드 활성화 → 채널 우클릭 → "ID 복사" → `.env`의 `CHANNEL_ID`

## 실행

```bash
source venv/bin/activate
python bot.py
```

## systemd 상시 실행 등록

`job-notifier.service` 파일의 `User`, `WorkingDirectory`, `ExecStart` 경로를 본인 환경에 맞게 수정한 뒤 등록합니다.

```bash
sudo cp job-notifier.service /etc/systemd/system/job-notifier.service
sudo systemctl daemon-reload
sudo systemctl enable --now job-notifier

# 상태 확인
sudo systemctl status job-notifier

# 로그 실시간 확인
journalctl -u job-notifier -f
```

## 동작 방식

- 매일 `NOTIFY_HOUR:NOTIFY_MINUTE` 시각에 DB를 조회합니다.
- 조건: `apply = 'PENDING'` AND 당일 크롤링(`DATE(crawled_at) = CURDATE()`) AND `TARGET_JOB_PARTS` 직무.
- 조회 결과를 직무별로 묶어 디스코드 임베드 메시지로 전송합니다.

## 참고

- `post_id UNIQUE` 제약으로 중복 공고는 DB 단계에서 제거되고, `DATE(crawled_at) = CURDATE()` 조건으로 당일 신규만 전송합니다.
- 알림 후 재전송을 완전히 막으려면 `notified` 컬럼을 추가해 전송 후 UPDATE하는 방식이 더 정확합니다.
- 테스트 시 `on_ready` 안에서 `await send_notification()`을 직접 호출하면 즉시 확인할 수 있습니다.

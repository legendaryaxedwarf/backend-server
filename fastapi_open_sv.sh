#!/usr/bin/env bash
#
# fastapi_open_sv.sh
# -------------------------------------------------------------
# Ubuntu 24.04 환경에서 Python만 설치되어 있다는 가정 하에
# FastAPI 서버를 한번에 세팅하고 실행하는 스크립트
#
# 사용법:
#   chmod +x fastapi_open_sv.sh
#   ./fastapi_open_sv.sh
#
# 옵션(환경변수로 조절 가능):
#   APP_DIR   서버 프로젝트 디렉토리 (기본: ./fastapi_app)
#   HOST      바인딩 호스트 (기본: 0.0.0.0)
#   PORT      바인딩 포트 (기본: 8000)
#   RELOAD    자동 리로드 여부 true/false (기본: true)
#
# 예)
#   PORT=9000 ./fastapi_open_sv.sh
# -------------------------------------------------------------

set -euo pipefail

# ---------- 설정값 ----------
APP_DIR="${APP_DIR:-./fastapi_app}"
HOST="${HOST:-0.0.0.0}"
PORT="${PORT:-8000}"
RELOAD="${RELOAD:-true}"
VENV_DIR="${APP_DIR}/venv"

echo "=================================================="
echo " FastAPI 서버 세팅 시작"
echo " APP_DIR : ${APP_DIR}"
echo " HOST    : ${HOST}"
echo " PORT    : ${PORT}"
echo " RELOAD  : ${RELOAD}"
echo "=================================================="

# ---------- 1. 필수 패키지 설치 (apt) ----------
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] python3 명령어를 찾을 수 없습니다. 먼저 python3를 설치해주세요."
    exit 1
fi

echo "[1/5] 시스템 패키지 업데이트 및 필수 도구 설치 확인 중..."
NEED_APT_INSTALL=false
for pkg in python3-venv python3-pip; do
    if ! dpkg -s "$pkg" &> /dev/null; then
        NEED_APT_INSTALL=true
    fi
done

if [ "$NEED_APT_INSTALL" = true ]; then
    echo "  -> python3-venv / python3-pip 설치가 필요합니다. sudo 권한이 필요할 수 있습니다."
    sudo apt-get update -y
    sudo apt-get install -y python3-venv python3-pip
else
    echo "  -> 필수 도구가 이미 설치되어 있습니다."
fi

# ---------- 2. 프로젝트 디렉토리 생성 ----------
echo "[2/5] 프로젝트 디렉토리 준비 중: ${APP_DIR}"
mkdir -p "${APP_DIR}"

# ---------- 3. 가상환경(venv) 생성 ----------
if [ ! -d "${VENV_DIR}" ]; then
    echo "[3/5] 가상환경 생성 중: ${VENV_DIR}"
    python3 -m venv "${VENV_DIR}"
else
    echo "[3/5] 가상환경이 이미 존재합니다. 재사용합니다: ${VENV_DIR}"
fi

# shellcheck disable=SC1091
source "${VENV_DIR}/bin/activate"

# ---------- 4. FastAPI / Uvicorn 설치 ----------
echo "[4/5] pip 업그레이드 및 FastAPI, Uvicorn 설치 중..."
pip install --upgrade pip --quiet
pip install --quiet "fastapi" "uvicorn[standard]"

# ---------- 5. 샘플 main.py 생성 (없을 경우에만) ----------
MAIN_PY="${APP_DIR}/main.py"
if [ ! -f "${MAIN_PY}" ]; then
    echo "[5/5] 샘플 main.py 생성 중: ${MAIN_PY}"
    cat > "${MAIN_PY}" << 'EOF'
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "FastAPI 서버가 정상적으로 실행 중입니다."}

@app.get("/health")
def health_check():
    return {"status": "ok"}
EOF
else
    echo "[5/5] 기존 main.py 파일을 사용합니다: ${MAIN_PY}"
fi

# ---------- 방화벽(ufw) 포트 오픈 (설치되어 있는 경우만) ----------
if command -v ufw &> /dev/null; then
    if sudo ufw status | grep -q "active"; then
        echo "[방화벽] ufw가 활성화되어 있어 포트 ${PORT}를 허용합니다."
        sudo ufw allow "${PORT}/tcp" || true
    fi
fi

# ---------- 서버 실행 ----------
RELOAD_FLAG=""
if [ "${RELOAD}" = "true" ]; then
    RELOAD_FLAG="--reload"
fi

echo "=================================================="
echo " 서버를 실행합니다: http://${HOST}:${PORT}"
echo " 종료하려면 Ctrl + C 를 누르세요."
echo "=================================================="

cd "${APP_DIR}"
exec uvicorn main:app --host "${HOST}" --port "${PORT}" ${RELOAD_FLAG}

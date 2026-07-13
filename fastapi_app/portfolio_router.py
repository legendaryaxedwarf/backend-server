import os
import uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel

from database import get_connection
from deps import get_current_member

router = APIRouter()

# nginx가 정적 파일을 서빙하는 WEB_ROOT 하위에 업로드 파일을 저장해서,
# 이후 브라우저에서 portfolio_img/portfolio_url을 그대로 <img src>, <a href>로 쓸 수 있게 함
UPLOAD_DIR = os.getenv("PORTFOLIO_UPLOAD_DIR", "/var/www/html/uploads/portfolio")
UPLOAD_URL_PREFIX = os.getenv("PORTFOLIO_UPLOAD_URL_PREFIX", "/uploads/portfolio")

os.makedirs(UPLOAD_DIR, exist_ok=True)


def _save_upload(upload: UploadFile) -> str:
    ext = os.path.splitext(upload.filename or "")[1]
    filename = f"{uuid.uuid4().hex}{ext}"
    dest_path = os.path.join(UPLOAD_DIR, filename)
    with open(dest_path, "wb") as f:
        f.write(upload.file.read())
    return f"{UPLOAD_URL_PREFIX}/{filename}"


class CnameRequest(BaseModel):
    cname: str
    portfolio_url: str | None = None


# =========================================================
# 포트폴리오 이미지/파일 업로드 (내 것만)
# =========================================================
@router.post("/users/me/portfolio")
def upload_portfolio(
    image: UploadFile | None = File(default=None),
    file: UploadFile | None = File(default=None),
    current_member: dict = Depends(get_current_member),
):
    if image is None and file is None:
        raise HTTPException(
            status_code=400,
            detail={"code": "INVALID_INPUT", "message": "이미지 또는 파일을 하나 이상 업로드해야 합니다."},
        )

    portfolio_img = _save_upload(image) if image else None
    portfolio_file = _save_upload(file) if file else None

    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            if portfolio_img and portfolio_file:
                cursor.execute(
                    "UPDATE members SET portfolio_img = %s, portfolio_file = %s WHERE member_id = %s",
                    (portfolio_img, portfolio_file, current_member["member_id"]),
                )
            elif portfolio_img:
                cursor.execute(
                    "UPDATE members SET portfolio_img = %s WHERE member_id = %s",
                    (portfolio_img, current_member["member_id"]),
                )
            else:
                cursor.execute(
                    "UPDATE members SET portfolio_file = %s WHERE member_id = %s",
                    (portfolio_file, current_member["member_id"]),
                )
            conn.commit()
    finally:
        conn.close()

    return {
        "success": True,
        "data": {"portfolio_img": portfolio_img, "portfolio_file": portfolio_file},
    }


# =========================================================
# 별칭(cname) / 포트폴리오 URL 등록·변경 (내 것만)
# =========================================================
@router.put("/users/me/cname")
def update_cname(body: CnameRequest, current_member: dict = Depends(get_current_member)):
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT member_id FROM members WHERE cname = %s AND member_id != %s",
                (body.cname, current_member["member_id"]),
            )
            if cursor.fetchone():
                raise HTTPException(
                    status_code=409,
                    detail={"code": "CNAME_DUPLICATED", "message": "이미 사용 중인 별칭입니다."},
                )

            cursor.execute(
                "UPDATE members SET cname = %s, portfolio_url = %s WHERE member_id = %s",
                (body.cname, body.portfolio_url, current_member["member_id"]),
            )
            conn.commit()
    finally:
        conn.close()

    return {"success": True, "data": {"cname": body.cname, "portfolio_url": body.portfolio_url}}


# =========================================================
# 별칭(cname)으로 포트폴리오 공개 조회 (인증 불필요, 외부 방문자용)
# =========================================================
@router.get("/portfolios/{cname}")
def get_public_portfolio(cname: str):
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT member_id, nickname, portfolio_img, portfolio_url FROM members WHERE cname = %s",
                (cname,),
            )
            member = cursor.fetchone()
    finally:
        conn.close()

    if not member:
        raise HTTPException(
            status_code=404,
            detail={"code": "PORTFOLIO_NOT_FOUND", "message": "존재하지 않는 포트폴리오입니다."},
        )

    return {"success": True, "data": member}

import os
import datetime
import bcrypt
import jwt  # PyJWT
from dotenv import load_dotenv

load_dotenv()

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_HOURS = 24  # 유효기간 1일


# =========================================================
# 비밀번호 해싱
# =========================================================
def hash_password(plain_password: str) -> str:
    """회원가입 시 비밀번호를 해싱해서 DB에 저장할 값으로 변환."""
    hashed = bcrypt.hashpw(plain_password.encode("utf-8"), bcrypt.gensalt())
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """로그인 시 입력한 비밀번호와 DB에 저장된 해시값을 비교."""
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))


# =========================================================
# JWT 발급 / 검증
# =========================================================
def create_access_token(member_id: int, email: str, nickname: str) -> str:
    """
    로그인 성공 시 호출. member_id/email/nickname을 payload에 담아 서명한 토큰을 반환.
    비밀번호 등 민감정보는 절대 payload에 넣지 않는다 (서명만 되고 암호화는 안 되어 누구나 디코딩 가능).
    """
    if not JWT_SECRET_KEY:
        raise RuntimeError("JWT_SECRET_KEY가 .env에 설정되어 있지 않습니다.")

    now = datetime.datetime.now(datetime.timezone.utc)
    payload = {
        "member_id": member_id,
        "email": email,
        "nickname": nickname,
        "iat": now,
        "exp": now + datetime.timedelta(hours=JWT_EXPIRE_HOURS),
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> dict | None:
    """
    토큰 서명/만료 검증 후 payload(dict)를 반환.
    서명이 위조됐거나 만료됐으면 None을 반환.
    """
    try:
        return jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

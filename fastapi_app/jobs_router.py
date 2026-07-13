from fastapi import APIRouter, Depends, HTTPException, Query

from database import get_connection
from deps import get_current_member

router = APIRouter()


# =========================================================
# 채용공고 목록 조회 (+ 로그인한 회원의 지원 상태 함께)
# =========================================================
@router.get("/jobs")
def list_jobs(
    job_part: str | None = Query(default=None, description="직무 필터 (부분일치)"),
    region: str | None = Query(default=None, description="지역 필터 (부분일치)"),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    current_member: dict = Depends(get_current_member),
):
    offset = (page - 1) * size

    where_clauses = []
    params: list = []

    if job_part:
        where_clauses.append("j.job_part LIKE %s")
        params.append(f"%{job_part}%")
    if region:
        where_clauses.append("j.region LIKE %s")
        params.append(f"%{region}%")

    where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

    query = f"""
        SELECT
            j.job_id, j.source, j.job_part, j.company_name, j.post_title,
            j.region, j.personal_history, j.pay, j.end_at, j.crawled_at,
            j.job_url, j.post_id,
            COALESCE(mja.apply, 'PENDING') AS my_apply_status
        FROM job j
        LEFT JOIN member_job_apply mja
            ON mja.job_id = j.job_id AND mja.member_id = %s
        {where_sql}
        ORDER BY j.crawled_at DESC
        LIMIT %s OFFSET %s
    """
    query_params = [current_member["member_id"], *params, size, offset]

    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(query, query_params)
            jobs = cursor.fetchall()
    finally:
        conn.close()

    # end_at, crawled_at은 date/datetime 객체라 JSON으로 바로 못 보내므로 문자열로 변환
    for job in jobs:
        if job.get("end_at") is not None:
            job["end_at"] = job["end_at"].strftime("%Y-%m-%d")
        if job.get("crawled_at") is not None:
            job["crawled_at"] = job["crawled_at"].strftime("%Y-%m-%d %H:%M:%S")

    return {"success": True, "data": {"jobs": jobs, "page": page, "size": size}}


# =========================================================
# 지원 여부 토글 (PENDING <-> APPLY)
# =========================================================
@router.patch("/jobs/{post_id}/apply")
def toggle_apply(post_id: str, current_member: dict = Depends(get_current_member)):
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            # post_id -> job_id 조회
            cursor.execute("SELECT job_id FROM job WHERE post_id = %s", (post_id,))
            job = cursor.fetchone()
            if not job:
                raise HTTPException(
                    status_code=404,
                    detail={"code": "JOB_NOT_FOUND", "message": "존재하지 않는 공고입니다."},
                )
            job_id = job["job_id"]

            # 현재 지원 상태 조회 (없으면 PENDING으로 간주)
            cursor.execute(
                "SELECT apply FROM member_job_apply WHERE member_id = %s AND job_id = %s",
                (current_member["member_id"], job_id),
            )
            current = cursor.fetchone()
            current_apply = current["apply"] if current else "PENDING"
            new_apply = "PENDING" if current_apply == "APPLY" else "APPLY"

            # UPSERT
            cursor.execute(
                """
                INSERT INTO member_job_apply (member_id, job_id, apply, applied_at)
                VALUES (%s, %s, %s, CASE WHEN %s = 'APPLY' THEN NOW() ELSE NULL END)
                ON DUPLICATE KEY UPDATE
                    apply = VALUES(apply),
                    applied_at = CASE WHEN VALUES(apply) = 'APPLY' THEN NOW() ELSE applied_at END
                """,
                (current_member["member_id"], job_id, new_apply, new_apply),
            )
            conn.commit()
    finally:
        conn.close()

    return {"success": True, "data": {"post_id": post_id, "apply": new_apply}}

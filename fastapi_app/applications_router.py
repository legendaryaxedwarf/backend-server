from fastapi import APIRouter, Depends, Query

from database import get_connection
from deps import get_current_member

router = APIRouter()


# =========================================================
# 내 지원 현황 목록 조회 (member_job_apply + job 조인)
# =========================================================
@router.get("/users/me/applications")
def list_my_applications(
    apply: str | None = Query(default=None, description="상태 필터 (PENDING/APPLY)"),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    current_member: dict = Depends(get_current_member),
):
    offset = (page - 1) * size

    where_clauses = ["mja.member_id = %s"]
    params: list = [current_member["member_id"]]

    if apply:
        where_clauses.append("mja.apply = %s")
        params.append(apply)

    where_sql = f"WHERE {' AND '.join(where_clauses)}"

    query = f"""
        SELECT
            mja.id, mja.apply, mja.applied_at, mja.created_at,
            j.job_id, j.post_id, j.source, j.job_part, j.company_name,
            j.post_title, j.region, j.pay, j.end_at, j.job_url
        FROM member_job_apply mja
        JOIN job j ON j.job_id = mja.job_id
        {where_sql}
        ORDER BY mja.created_at DESC
        LIMIT %s OFFSET %s
    """
    query_params = [*params, size, offset]

    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(query, query_params)
            applications = cursor.fetchall()
    finally:
        conn.close()

    # datetime/date 객체는 JSON으로 바로 못 보내므로 문자열로 변환
    for app in applications:
        if app.get("applied_at") is not None:
            app["applied_at"] = app["applied_at"].strftime("%Y-%m-%d %H:%M:%S")
        if app.get("created_at") is not None:
            app["created_at"] = app["created_at"].strftime("%Y-%m-%d %H:%M:%S")
        if app.get("end_at") is not None:
            app["end_at"] = app["end_at"].strftime("%Y-%m-%d")

    return {
        "success": True,
        "data": {"applications": applications, "page": page, "size": size},
    }

import mysql.connector
from config import DB_CONFIG, TARGET_JOB_PARTS


def get_connection():
    return mysql.connector.connect(**DB_CONFIG)


def fetch_new_jobs():
    """
    아직 지원하지 않은(PENDING) 공고 중,
    지정한 직무 파트에 해당하는 공고를 조회.
    당일 크롤링된 것만 가져옴.
    """
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    query = """
        SELECT job_id, source, job_part, company_name,
               post_title, region, personal_history, pay,
               end_at, job_url, apply
        FROM job
        WHERE apply = 'PENDING'
          AND DATE(crawled_at) = CURDATE()
    """
    params = []

    if TARGET_JOB_PARTS:
        placeholders = ",".join(["%s"] * len(TARGET_JOB_PARTS))
        query += f" AND job_part IN ({placeholders})"
        params.extend(TARGET_JOB_PARTS)

    query += " ORDER BY job_part, crawled_at DESC"

    cursor.execute(query, params)
    rows = cursor.fetchall()

    cursor.close()
    conn.close()
    return rows

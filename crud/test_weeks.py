from typing import List, Optional, Dict, Any
from pymysql.connections import Connection

TABLE_NAME = "test_week_info"
TEST_WORDS_TABLE = "test_words"
WORD_BOOK_TABLE = "word_book"


def get_all_test_weeks(
    conn: Connection, limit: int = 10, order: str = "desc"
) -> List[Dict[str, Any]]:
    """시험 주차 목록을 조회합니다."""
    order_clause = "DESC" if order.lower() == "desc" else "ASC"

    sql = f"""
    SELECT
        twi.twi_id,
        twi.name,
        twi.start_date,
        twi.end_date,
        twi.test_start_datetime,
        twi.test_end_datetime,
        COUNT(tw.tw_id) as word_count,
        twi.created_at,
        twi.updated_at
    FROM {TABLE_NAME} twi
    LEFT JOIN {TEST_WORDS_TABLE} tw ON twi.twi_id = tw.twi_id
    GROUP BY twi.twi_id, twi.name, twi.start_date, twi.end_date, twi.test_start_datetime, twi.test_end_datetime, twi.created_at, twi.updated_at
    ORDER BY twi.start_date {order_clause}
    LIMIT %s;
    """
    with conn.cursor() as cursor:
        cursor.execute(sql, (limit,))
        return cursor.fetchall()


def get_test_week_by_id(conn: Connection, twi_id: int) -> Optional[Dict[str, Any]]:
    """특정 시험 주차 정보를 조회합니다."""
    sql = f"""
    SELECT twi_id, name, start_date, end_date, test_start_datetime, test_end_datetime, created_at, updated_at
    FROM {TABLE_NAME}
    WHERE twi_id = %s;
    """
    with conn.cursor() as cursor:
        cursor.execute(sql, (twi_id,))
        return cursor.fetchone()


def get_test_week_words(conn: Connection, twi_id: int) -> List[Dict[str, Any]]:
    """특정 주차의 단어 목록을 조회합니다 (word_book과 JOIN)."""
    sql = f"""
    SELECT
        tw.tw_id,
        tw.wb_id,
        wb.word_english,
        wb.word_meaning,
        wb.date
    FROM {TEST_WORDS_TABLE} tw
    JOIN {WORD_BOOK_TABLE} wb ON tw.wb_id = wb.wb_id
    WHERE tw.twi_id = %s
    ORDER BY wb.date ASC, tw.tw_id ASC;
    """
    with conn.cursor() as cursor:
        cursor.execute(sql, (twi_id,))
        return cursor.fetchall()

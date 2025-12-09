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
        twi.TWI_ID,
        twi.NAME,
        twi.START_DATE,
        twi.END_DATE,
        twi.TEST_START_DATETIME,
        twi.TEST_END_DATETIME,
        (
            SELECT COUNT(*)
            FROM {WORD_BOOK_TABLE} wb
            WHERE wb.DATE BETWEEN twi.START_DATE AND twi.END_DATE
        ) as word_count,
        twi.CREATED_AT,
        twi.UPDATED_AT
    FROM {TABLE_NAME} twi
    HAVING word_count > 0
    ORDER BY twi.START_DATE {order_clause}
    LIMIT %s;
    """
    with conn.cursor() as cursor:
        cursor.execute(sql, (limit,))
        return cursor.fetchall()


def get_test_week_by_id(conn: Connection, twi_id: int) -> Optional[Dict[str, Any]]:
    """특정 시험 주차 정보를 조회합니다."""
    sql = f"""
    SELECT TWI_ID, NAME, START_DATE, END_DATE, TEST_START_DATETIME, TEST_END_DATETIME, CREATED_AT, UPDATED_AT
    FROM {TABLE_NAME}
    WHERE TWI_ID = %s;
    """
    with conn.cursor() as cursor:
        cursor.execute(sql, (twi_id,))
        return cursor.fetchone()


def get_test_week_words(conn: Connection, twi_id: int) -> List[Dict[str, Any]]:
    """특정 주차의 단어 목록을 조회합니다 (word_book과 JOIN)."""
    sql = f"""
    SELECT
        tw.TW_ID,
        tw.WB_ID,
        wb.WORD_ENGLISH,
        wb.WORD_MEANING,
        wb.DATE
    FROM {TEST_WORDS_TABLE} tw
    JOIN {WORD_BOOK_TABLE} wb ON tw.WB_ID = wb.WB_ID
    WHERE tw.TWI_ID = %s
    ORDER BY wb.DATE ASC, tw.TW_ID ASC;
    """
    with conn.cursor() as cursor:
        cursor.execute(sql, (twi_id,))
        return cursor.fetchall()

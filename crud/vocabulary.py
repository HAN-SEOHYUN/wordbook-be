from typing import List, Optional, Dict, Any
from pymysql.connections import Connection
from schemas.vocabulary import VocabularyCreate, VocabularyUpdate
from datetime import date

TABLE_NAME = "daily_vocabulary"


def create_or_update_word(
    conn: Connection, word: VocabularyCreate
) -> Optional[Dict[str, Any]]:
    """
    단어를 UPSERT(Insert or Update)합니다.
    - (date, english_word)가 고유 키로 중복되면 korean_meaning, source_url 및 updated_at을 업데이트합니다.
    """
    sql = f"""
    INSERT INTO {TABLE_NAME} (date, english_word, korean_meaning, source_url)
    VALUES (%s, %s, %s, %s)
    ON DUPLICATE KEY UPDATE
        korean_meaning = VALUES(korean_meaning),
        source_url = VALUES(source_url),
        updated_at = CURRENT_TIMESTAMP;
    """

    try:
        with conn.cursor() as cursor:
            cursor.execute(sql, (word.date, word.english_word, word.korean_meaning, word.source_url))
            conn.commit()

            # 마지막으로 삽입/업데이트된 행의 ID를 가져옵니다.
            # MySQL의 LAST_INSERT_ID()는 INSERT 시에만 유효하므로,
            # UPSERT 후에는 UNIQUE KEY를 사용하여 데이터를 다시 조회합니다.

            select_sql = f"""
            SELECT id, date, english_word, korean_meaning, source_url, created_at, updated_at
            FROM {TABLE_NAME}
            WHERE date = %s AND english_word = %s
            """
            cursor.execute(select_sql, (word.date, word.english_word))
            return cursor.fetchone()

    except Exception as e:
        conn.rollback()
        raise e


def get_word_by_id(conn: Connection, word_id: int) -> Optional[Dict[str, Any]]:
    """ID를 사용하여 단어 정보를 조회합니다."""
    sql = f"""
    SELECT id, date, english_word, korean_meaning, source_url, created_at, updated_at
    FROM {TABLE_NAME}
    WHERE id = %s;
    """
    with conn.cursor() as cursor:
        cursor.execute(sql, (word_id,))
        return cursor.fetchone()


def get_words(
    conn: Connection,
    limit: int = 100,
    offset: int = 0,
    target_date: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    단어 목록을 조회합니다. 날짜 필터링 및 페이징을 지원합니다.
    """
    sql = f"""
    SELECT id, date, english_word, korean_meaning, source_url, created_at, updated_at
    FROM {TABLE_NAME}
    """
    params: List[Any] = []
    where_clause = []

    if target_date:
        # 날짜 포맷 검증은 Service/Router에서 수행되었다고 가정
        where_clause.append("date = %s")
        params.append(target_date)

    if where_clause:
        sql += " WHERE " + " AND ".join(where_clause)

    sql += " ORDER BY date DESC, id DESC LIMIT %s OFFSET %s;"
    params.extend([limit, offset])

    with conn.cursor() as cursor:
        cursor.execute(sql, tuple(params))
        return cursor.fetchall()


def update_word(
    conn: Connection, word_id: int, word_data: VocabularyUpdate
) -> Optional[Dict[str, Any]]:
    """
    단어 ID를 기반으로 korean_meaning, english_word, source_url을 업데이트합니다.
    """
    sql = f"""
    UPDATE {TABLE_NAME}
    SET
        english_word = %s,
        korean_meaning = %s,
        source_url = %s,
        updated_at = CURRENT_TIMESTAMP
    WHERE id = %s;
    """
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                sql, (word_data.english_word, word_data.korean_meaning, word_data.source_url, word_id)
            )
            conn.commit()
            if cursor.rowcount == 0:
                return None

            # 업데이트된 데이터 조회 (DictCursor 덕분에 딕셔너리로 반환됨)
            return get_word_by_id(conn, word_id)

    except Exception as e:
        conn.rollback()
        raise e


def delete_word(conn: Connection, word_id: int) -> bool:
    """단어 ID를 기반으로 단어를 삭제합니다."""
    sql = f"DELETE FROM {TABLE_NAME} WHERE id = %s;"
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql, (word_id,))
            conn.commit()
            return cursor.rowcount > 0  # 삭제 성공 여부 반환
    except Exception as e:
        conn.rollback()
        raise e


def get_distinct_dates(conn, limit: int = 5):
    """
    데이터베이스에서 고유한 날짜 목록을 최신순으로 조회합니다.
    """
    cursor = conn.cursor()

    query = f"""
        SELECT DISTINCT date 
        FROM {TABLE_NAME}
        ORDER BY date DESC 
        LIMIT %s
    """

    cursor.execute(query, (limit,))
    rows = cursor.fetchall()

    # 각 row에서 날짜만 추출하여 반환
    return rows

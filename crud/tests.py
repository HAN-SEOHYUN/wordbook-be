from typing import List, Optional, Dict, Any
from pymysql.connections import Connection
import re

TEST_RESULT_TABLE = "test_result"
TEST_ANSWERS_TABLE = "test_answers"
TEST_WORDS_TABLE = "test_words"
WORD_BOOK_TABLE = "word_book"
TEST_WEEK_INFO_TABLE = "test_week_info"
USERS_TABLE = "users"


def normalize_answer(text: str) -> str:
    """답안 정규화: 대소문자 무시, 특수문자 제거"""
    return re.sub(r'[^a-z0-9\s]', '', text.lower().strip())


def get_existing_test_result(
    conn: Connection, u_id: int, twi_id: int
) -> Optional[Dict[str, Any]]:
    """기존 시험 결과 조회 (재시험 체크용)"""
    sql = f"""
    SELECT tr_id, u_id, twi_id, test_score, created_at, updated_at
    FROM {TEST_RESULT_TABLE}
    WHERE u_id = %s AND twi_id = %s;
    """
    with conn.cursor() as cursor:
        cursor.execute(sql, (u_id, twi_id))
        return cursor.fetchone()


def create_test_result(conn: Connection, u_id: int, twi_id: int) -> int:
    """새 시험 결과 레코드 생성"""
    sql = f"""
    INSERT INTO {TEST_RESULT_TABLE} (u_id, twi_id, test_score)
    VALUES (%s, %s, NULL);
    """
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql, (u_id, twi_id))
            conn.commit()
            return cursor.lastrowid
    except Exception as e:
        conn.rollback()
        raise e


def reset_test_result(conn: Connection, tr_id: int) -> None:
    """시험 점수 초기화 및 기존 답안 삭제 (재시험용)"""
    try:
        with conn.cursor() as cursor:
            # 기존 답안 삭제
            cursor.execute(f"DELETE FROM {TEST_ANSWERS_TABLE} WHERE tr_id = %s;", (tr_id,))
            # 점수 초기화
            cursor.execute(
                f"UPDATE {TEST_RESULT_TABLE} SET test_score = NULL, updated_at = CURRENT_TIMESTAMP WHERE tr_id = %s;",
                (tr_id,)
            )
            conn.commit()
    except Exception as e:
        conn.rollback()
        raise e


def get_correct_answers_for_test(conn: Connection, tr_id: int) -> Dict[int, Dict[str, str]]:
    """시험의 정답 목록 조회 (tw_id를 키로 하는 딕셔너리 반환)"""
    sql = f"""
    SELECT tw.tw_id, wb.word_english, wb.word_meaning
    FROM {TEST_RESULT_TABLE} tr
    JOIN {TEST_WORDS_TABLE} tw ON tr.twi_id = tw.twi_id
    JOIN {WORD_BOOK_TABLE} wb ON tw.wb_id = wb.wb_id
    WHERE tr.tr_id = %s;
    """
    with conn.cursor() as cursor:
        cursor.execute(sql, (tr_id,))
        rows = cursor.fetchall()

        # tw_id를 키로 하는 딕셔너리로 변환
        return {
            row['tw_id']: {
                'word_english': row['word_english'],
                'word_meaning': row['word_meaning']
            }
            for row in rows
        }


def save_answer(
    conn: Connection, tr_id: int, tw_id: int, user_answer: str, is_correct: bool
) -> int:
    """답안 저장 (UPSERT)"""
    sql = f"""
    INSERT INTO {TEST_ANSWERS_TABLE} (tr_id, tw_id, user_answer, is_correct)
    VALUES (%s, %s, %s, %s)
    ON DUPLICATE KEY UPDATE
        user_answer = VALUES(user_answer),
        is_correct = VALUES(is_correct),
        updated_at = CURRENT_TIMESTAMP;
    """
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql, (tr_id, tw_id, user_answer, is_correct))
            conn.commit()

            # 저장된 ta_id 조회
            cursor.execute(
                f"SELECT ta_id FROM {TEST_ANSWERS_TABLE} WHERE tr_id = %s AND tw_id = %s;",
                (tr_id, tw_id)
            )
            result = cursor.fetchone()
            return result['ta_id'] if result else cursor.lastrowid
    except Exception as e:
        conn.rollback()
        raise e


def update_test_score(conn: Connection, tr_id: int, score: int) -> None:
    """시험 점수 업데이트"""
    sql = f"""
    UPDATE {TEST_RESULT_TABLE}
    SET test_score = %s, updated_at = CURRENT_TIMESTAMP
    WHERE tr_id = %s;
    """
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql, (score, tr_id))
            conn.commit()
    except Exception as e:
        conn.rollback()
        raise e


def get_test_history(conn: Connection, u_id: int) -> List[Dict[str, Any]]:
    """사용자의 시험 기록 히스토리 조회"""
    sql = f"""
    SELECT
        tr.tr_id,
        tr.u_id,
        tr.twi_id,
        tr.test_score,
        tr.created_at,
        tr.updated_at,
        twi.name AS week_name,
        twi.start_date,
        twi.end_date,
        DATE(twi.test_start_datetime) AS test_date,
        COUNT(ta.ta_id) AS total_questions,
        SUM(ta.is_correct) AS correct_count
    FROM {TEST_RESULT_TABLE} tr
    JOIN {TEST_WEEK_INFO_TABLE} twi ON tr.twi_id = twi.twi_id
    LEFT JOIN {TEST_ANSWERS_TABLE} ta ON tr.tr_id = ta.tr_id
    WHERE tr.u_id = %s AND tr.test_score IS NOT NULL
    GROUP BY tr.tr_id, tr.u_id, tr.twi_id, tr.test_score, tr.created_at, tr.updated_at,
             twi.name, twi.start_date, twi.end_date, twi.test_start_datetime
    ORDER BY tr.created_at DESC;
    """
    with conn.cursor() as cursor:
        cursor.execute(sql, (u_id,))
        return cursor.fetchall()


def get_test_detail(conn: Connection, tr_id: int) -> Optional[Dict[str, Any]]:
    """특정 시험의 상세 결과 조회 (기본 정보 + 문항별 답안)"""
    # 1. 시험 기본 정보 조회
    basic_sql = f"""
    SELECT
        tr.tr_id,
        tr.u_id,
        u.username,
        tr.twi_id,
        twi.name AS week_name,
        tr.test_score,
        tr.created_at AS test_date,
        COUNT(ta.ta_id) AS total_questions,
        SUM(ta.is_correct) AS correct_count
    FROM {TEST_RESULT_TABLE} tr
    JOIN {USERS_TABLE} u ON tr.u_id = u.u_id
    JOIN {TEST_WEEK_INFO_TABLE} twi ON tr.twi_id = twi.twi_id
    LEFT JOIN {TEST_ANSWERS_TABLE} ta ON tr.tr_id = ta.tr_id
    WHERE tr.tr_id = %s
    GROUP BY tr.tr_id, tr.u_id, u.username, tr.twi_id, twi.name, tr.test_score, tr.created_at;
    """

    # 2. 문항별 답안 조회
    answers_sql = f"""
    SELECT
        ta.ta_id,
        ta.tw_id,
        ta.user_answer,
        ta.is_correct,
        wb.word_english,
        wb.word_meaning
    FROM {TEST_ANSWERS_TABLE} ta
    JOIN {TEST_WORDS_TABLE} tw ON ta.tw_id = tw.tw_id
    JOIN {WORD_BOOK_TABLE} wb ON tw.wb_id = wb.wb_id
    WHERE ta.tr_id = %s
    ORDER BY ta.ta_id;
    """

    with conn.cursor() as cursor:
        # 기본 정보 조회
        cursor.execute(basic_sql, (tr_id,))
        basic_info = cursor.fetchone()

        if not basic_info:
            return None

        # 문항별 답안 조회
        cursor.execute(answers_sql, (tr_id,))
        answers = cursor.fetchall()

        # 결과 조합
        result = dict(basic_info)
        result['answers'] = answers

        return result

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
    SELECT TR_ID, U_ID, TWI_ID, TEST_SCORE, CREATED_AT, UPDATED_AT
    FROM {TEST_RESULT_TABLE}
    WHERE U_ID = %s AND TWI_ID = %s;
    """
    with conn.cursor() as cursor:
        cursor.execute(sql, (u_id, twi_id))
        return cursor.fetchone()


def create_test_result(conn: Connection, u_id: int, twi_id: int) -> int:
    """새 시험 결과 레코드 생성"""
    sql = f"""
    INSERT INTO {TEST_RESULT_TABLE} (U_ID, TWI_ID, TEST_SCORE)
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
            cursor.execute(f"DELETE FROM {TEST_ANSWERS_TABLE} WHERE TR_ID = %s;", (tr_id,))
            # 점수 초기화
            cursor.execute(
                f"UPDATE {TEST_RESULT_TABLE} SET TEST_SCORE = NULL, UPDATED_AT = CURRENT_TIMESTAMP WHERE TR_ID = %s;",
                (tr_id,)
            )
            conn.commit()
    except Exception as e:
        conn.rollback()
        raise e


def get_correct_answers_for_test(conn: Connection, tr_id: int) -> Dict[int, Dict[str, str]]:
    """시험의 정답 목록 조회 (tw_id를 키로 하는 딕셔너리 반환)"""
    sql = f"""
    SELECT tw.TW_ID, wb.WORD_ENGLISH, wb.WORD_MEANING
    FROM {TEST_RESULT_TABLE} tr
    JOIN {TEST_WORDS_TABLE} tw ON tr.TWI_ID = tw.TWI_ID
    JOIN {WORD_BOOK_TABLE} wb ON tw.WB_ID = wb.WB_ID
    WHERE tr.TR_ID = %s;
    """
    with conn.cursor() as cursor:
        cursor.execute(sql, (tr_id,))
        rows = cursor.fetchall()

        # tw_id를 키로 하는 딕셔너리로 변환
        return {
            row['TW_ID']: {
                'word_english': row['WORD_ENGLISH'],
                'word_meaning': row['WORD_MEANING']
            }
            for row in rows
        }


def save_answer(
    conn: Connection, tr_id: int, tw_id: int, user_answer: str, is_correct: bool
) -> int:
    """답안 저장 (UPSERT)"""
    sql = f"""
    INSERT INTO {TEST_ANSWERS_TABLE} (TR_ID, TW_ID, USER_ANSWER, IS_CORRECT)
    VALUES (%s, %s, %s, %s)
    ON DUPLICATE KEY UPDATE
        USER_ANSWER = VALUES(USER_ANSWER),
        IS_CORRECT = VALUES(IS_CORRECT),
        UPDATED_AT = CURRENT_TIMESTAMP;
    """
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql, (tr_id, tw_id, user_answer, is_correct))
            conn.commit()

            # 저장된 ta_id 조회
            cursor.execute(
                f"SELECT TA_ID FROM {TEST_ANSWERS_TABLE} WHERE TR_ID = %s AND TW_ID = %s;",
                (tr_id, tw_id)
            )
            result = cursor.fetchone()
            return result['TA_ID'] if result else cursor.lastrowid
    except Exception as e:
        conn.rollback()
        raise e


def update_test_score(conn: Connection, tr_id: int, score: int) -> None:
    """시험 점수 업데이트"""
    sql = f"""
    UPDATE {TEST_RESULT_TABLE}
    SET TEST_SCORE = %s, UPDATED_AT = CURRENT_TIMESTAMP
    WHERE TR_ID = %s;
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
        tr.TR_ID,
        tr.U_ID,
        tr.TWI_ID,
        tr.TEST_SCORE,
        tr.CREATED_AT,
        tr.UPDATED_AT,
        twi.NAME AS week_name,
        twi.START_DATE,
        twi.END_DATE,
        DATE(twi.TEST_START_DATETIME) AS test_date,
        COUNT(ta.TA_ID) AS total_questions,
        SUM(ta.IS_CORRECT) AS correct_count
    FROM {TEST_RESULT_TABLE} tr
    JOIN {TEST_WEEK_INFO_TABLE} twi ON tr.TWI_ID = twi.TWI_ID
    LEFT JOIN {TEST_ANSWERS_TABLE} ta ON tr.TR_ID = ta.TR_ID
    WHERE tr.U_ID = %s AND tr.TEST_SCORE IS NOT NULL
    GROUP BY tr.TR_ID, tr.U_ID, tr.TWI_ID, tr.TEST_SCORE, tr.CREATED_AT, tr.UPDATED_AT,
             twi.NAME, twi.START_DATE, twi.END_DATE, twi.TEST_START_DATETIME
    ORDER BY tr.CREATED_AT DESC;
    """
    with conn.cursor() as cursor:
        cursor.execute(sql, (u_id,))
        return cursor.fetchall()


def get_test_detail(conn: Connection, tr_id: int) -> Optional[Dict[str, Any]]:
    """특정 시험의 상세 결과 조회 (기본 정보 + 문항별 답안)"""
    # 1. 시험 기본 정보 조회
    basic_sql = f"""
    SELECT
        tr.TR_ID,
        tr.U_ID,
        u.USERNAME,
        tr.TWI_ID,
        twi.NAME AS week_name,
        tr.TEST_SCORE,
        tr.CREATED_AT AS test_date,
        COUNT(ta.TA_ID) AS total_questions,
        SUM(ta.IS_CORRECT) AS correct_count
    FROM {TEST_RESULT_TABLE} tr
    JOIN {USERS_TABLE} u ON tr.U_ID = u.U_ID
    JOIN {TEST_WEEK_INFO_TABLE} twi ON tr.TWI_ID = twi.TWI_ID
    LEFT JOIN {TEST_ANSWERS_TABLE} ta ON tr.TR_ID = ta.TR_ID
    WHERE tr.TR_ID = %s
    GROUP BY tr.TR_ID, tr.U_ID, u.USERNAME, tr.TWI_ID, twi.NAME, tr.TEST_SCORE, tr.CREATED_AT;
    """

    # 2. 문항별 답안 조회
    answers_sql = f"""
    SELECT
        ta.TA_ID,
        ta.TW_ID,
        ta.USER_ANSWER,
        ta.IS_CORRECT,
        wb.WORD_ENGLISH,
        wb.WORD_MEANING
    FROM {TEST_ANSWERS_TABLE} ta
    JOIN {TEST_WORDS_TABLE} tw ON ta.TW_ID = tw.TW_ID
    JOIN {WORD_BOOK_TABLE} wb ON tw.WB_ID = wb.WB_ID
    WHERE ta.TR_ID = %s
    ORDER BY ta.TA_ID;
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


def get_test_result_by_id(conn: Connection, tr_id: int) -> Optional[Dict[str, Any]]:
    """tr_id로 시험 결과 조회"""
    sql = f"""
    SELECT TR_ID, U_ID, TWI_ID, TEST_SCORE, CREATED_AT, UPDATED_AT
    FROM {TEST_RESULT_TABLE}
    WHERE TR_ID = %s;
    """
    with conn.cursor() as cursor:
        cursor.execute(sql, (tr_id,))
        return cursor.fetchone()


def delete_test_result(conn: Connection, tr_id: int) -> None:
    """시험 결과 삭제 (CASCADE로 test_answers도 함께 삭제됨)"""
    sql = f"""
    DELETE FROM {TEST_RESULT_TABLE}
    WHERE TR_ID = %s;
    """
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql, (tr_id,))
            conn.commit()
    except Exception as e:
        conn.rollback()
        raise e

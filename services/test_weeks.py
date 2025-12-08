from fastapi import HTTPException, status
from core.database import DatabaseManager
from schemas.test_weeks import (
    TestWeekResponse,
    TestWeekListResponse,
    TestWeekWordsResponse,
    TestWeekWordResponse,
)
from crud import test_weeks as crud_test_weeks


class TestWeekService:
    """시험 주차 관련 비즈니스 로직을 처리하는 서비스 클래스"""

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def get_all_test_weeks(self, limit: int = 10, order: str = "desc") -> TestWeekListResponse:
        """시험 주차 목록 조회"""
        try:
            with self.db.get_connection() as conn:
                db_weeks = crud_test_weeks.get_all_test_weeks(conn, limit, order)
                weeks = [TestWeekResponse(**week) for week in db_weeks]
                return TestWeekListResponse(weeks=weeks)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to fetch test weeks: {e}",
            )

    def get_test_week_words(self, twi_id: int) -> TestWeekWordsResponse:
        """특정 주차의 단어 목록 조회"""
        with self.db.get_connection() as conn:
            # 주차 정보 조회
            week_info = crud_test_weeks.get_test_week_by_id(conn, twi_id)
            if not week_info:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Test week with ID {twi_id} not found.",
                )

            # 단어 목록 조회
            db_words = crud_test_weeks.get_test_week_words(conn, twi_id)
            words = [TestWeekWordResponse(**word) for word in db_words]

            return TestWeekWordsResponse(
                twi_id=week_info['TWI_ID'],
                week_name=week_info['NAME'],
                start_date=week_info['START_DATE'],
                end_date=week_info['END_DATE'],
                test_start_datetime=week_info['TEST_START_DATETIME'],
                test_end_datetime=week_info['TEST_END_DATETIME'],
                words=words,
            )

from typing import List, Optional, Dict
from fastapi import HTTPException, status
from core.database import DatabaseManager
from schemas.vocabulary import VocabularyCreate, VocabularyUpdate, VocabularyResponse, VocabularyListResponse
from crud import vocabulary as crud_voca
from schemas.vocabulary import validate_date_format


class VocabularyService:
    """단어 관련 비즈니스 로직을 처리하는 서비스 클래스입니다."""

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def create_or_update_word(self, word_data: VocabularyCreate) -> VocabularyResponse:
        """새 단어를 저장하거나, 중복 시 업데이트합니다."""
        try:
            with self.db.get_connection() as conn:
                db_word = crud_voca.create_or_update_word(conn, word_data)

                if not db_word:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="Failed to create or update vocabulary item.",
                    )

                return VocabularyResponse.from_db_dict(db_word)
        except Exception as e:
            # DB 연결/쿼리 오류 발생 시 500 에러로 변환
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database operation failed: {e}",
            )

    def get_word(self, word_id: int) -> VocabularyResponse:
        """특정 ID의 단어를 조회합니다."""
        with self.db.get_connection() as conn:
            db_word = crud_voca.get_word_by_id(conn, word_id)

            if not db_word:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Vocabulary item with ID {word_id} not found.",
                )
            return VocabularyResponse.model_validate(db_word)

    def get_word_list(
        self, target_date: str, limit: int = 100, offset: int = 0
    ) -> VocabularyListResponse:
        """
        단어 목록을 조회합니다. target_date가 필수입니다.
        날짜, 대표 source_url, 단어 목록을 포함한 구조화된 응답을 반환합니다.
        """

        # 날짜 포맷 유효성 검사
        try:
            validate_date_format(target_date)
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

        with self.db.get_connection() as conn:
            # 단어 목록 조회
            db_words = crud_voca.get_words(conn, limit, offset, target_date)
            words = [VocabularyResponse.from_db_dict(word) for word in db_words]

            # 대표 source_url 조회 (null이 아닌 값 중 하나)
            source_url = crud_voca.get_representative_source_url(conn, target_date)

            # 새로운 응답 구조로 반환
            return VocabularyListResponse(
                date=target_date,
                source_url=source_url,
                words=words
            )

    def update_word(
        self, word_id: int, word_data: VocabularyUpdate
    ) -> VocabularyResponse:
        """단어 정보를 업데이트합니다."""
        try:
            with self.db.get_connection() as conn:
                db_word = crud_voca.update_word(conn, word_id, word_data)

                if not db_word:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Vocabulary item with ID {word_id} not found for update.",
                    )
                return VocabularyResponse.from_db_dict(db_word)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database update failed: {e}",
            )

    def delete_word(self, word_id: int) -> Dict[str, str]:
        """단어를 삭제합니다."""
        try:
            with self.db.get_connection() as conn:
                success = crud_voca.delete_word(conn, word_id)

                if not success:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Vocabulary item with ID {word_id} not found for deletion.",
                    )
                return {"message": "Vocabulary item successfully deleted."}
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database deletion failed: {e}",
            )

    def get_distinct_dates(self, limit: int = 5) -> List[str]:
        """
        이번주 토요일 시험 범위의 날짜 목록을 반환합니다.
        test_week_info의 가장 최근 주차의 start_date ~ end_date 범위 내 날짜만 반환합니다.

        Args:
            limit: 반환할 최대 날짜 개수 (기본값: 5, 사용되지 않음)

        Returns:
            날짜 문자열 리스트 (YYYY-MM-DD 형식, 최신순)
        """
        try:
            with self.db.get_connection() as conn:
                with conn.cursor() as cursor:
                    # 모든 등록된 단어의 날짜를 조회 (최신순)
                    date_query = """
                    SELECT DISTINCT DATE
                    FROM word_book
                    ORDER BY DATE DESC
                    """
                    cursor.execute(date_query)
                    rows = cursor.fetchall()

                    # 날짜 문자열 리스트로 변환
                    dates = [str(row["DATE"]) for row in rows]

                    return dates

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to fetch test week dates: {e}",
            )

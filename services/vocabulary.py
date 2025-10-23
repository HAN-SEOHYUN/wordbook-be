from typing import List, Optional, Dict
from fastapi import HTTPException, status
from core.database import DatabaseManager
from schemas.vocabulary import VocabularyCreate, VocabularyUpdate, VocabularyResponse
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

                return VocabularyResponse.model_validate(db_word)
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
    ) -> List[VocabularyResponse]:
        """
        단어 목록을 조회합니다. target_date가 필수입니다.
        """

        # 날짜 포맷 유효성 검사
        try:
            validate_date_format(target_date)
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

        with self.db.get_connection() as conn:
            db_words = crud_voca.get_words(conn, limit, offset, target_date)

            return [VocabularyResponse.model_validate(word) for word in db_words]

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
                return VocabularyResponse.model_validate(db_word)
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
        데이터베이스에 저장된 고유한 날짜 목록을 최신순으로 조회합니다.

        Args:
            limit: 반환할 최대 날짜 개수 (기본값: 5)

        Returns:
            날짜 문자열 리스트 (YYYY-MM-DD 형식, 최신순)
        """
        try:
            with self.db.get_connection() as conn:
                rows = crud_voca.get_distinct_dates(conn, limit)

                # DictCursor를 사용하므로 딕셔너리 형태로 반환됨
                # rows는 [{'date': datetime.date(2025, 1, 22)}, ...] 형태
                dates = [str(row["date"]) for row in rows]

                return dates
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to fetch distinct dates: {e}",
            )

from pydantic import BaseModel, field_validator, Field
from datetime import datetime, date
from typing import Optional, List


# 유틸리티: YYYY-MM-DD 형식 검증
def validate_date_format(value: str) -> str:
    try:
        # date.fromisoformat은 YYYY-MM-DD 형식만 받음
        date.fromisoformat(value)
        return value
    except ValueError:
        raise ValueError("Date must be in YYYY-MM-DD format.")


# Vocabulary DB 필드를 반영하는 기본 모델
class VocabularyBase(BaseModel):
    english_word: str = Field(
        ..., min_length=1, max_length=255, description="영단어 또는 구문 (최대 255자)"
    )
    korean_meaning: str = Field(..., min_length=1, description="한글 해석")
    source_url: Optional[str] = Field(
        None, max_length=1024, description="단어 출처 URL (최대 1024자)"
    )

    @field_validator("english_word", "korean_meaning")
    @classmethod
    def validate_not_empty(cls, v: str) -> str:
        """빈 문자열 또는 공백만 있는 경우 검증"""
        if not v or not v.strip():
            raise ValueError("필드는 비어있을 수 없습니다.")
        return v.strip()

    @field_validator("source_url")
    @classmethod
    def validate_source_url(cls, v: Optional[str]) -> Optional[str]:
        """source_url 검증 (선택적 필드)"""
        if v is not None:
            v = v.strip()
            if v and len(v) > 1024:
                raise ValueError("source_url은 최대 1024자까지 가능합니다.")
        return v


# 1. 생성 요청 (POST /) 모델
class VocabularyCreate(VocabularyBase):
    date: str  # YYYY-MM-DD

    @field_validator("date")
    @classmethod
    def check_date_format(cls, v: str) -> str:
        return validate_date_format(v)


# 2. 업데이트 요청 (PUT /{word_id}) 모델
# source_url을 제외하고 english_word와 korean_meaning만 업데이트
class VocabularyUpdate(BaseModel):
    english_word: str = Field(
        ..., min_length=1, max_length=255, description="영단어 또는 구문 (최대 255자)"
    )
    korean_meaning: str = Field(..., min_length=1, description="한글 해석")

    @field_validator("english_word", "korean_meaning")
    @classmethod
    def validate_not_empty(cls, v: str) -> str:
        """빈 문자열 또는 공백만 있는 경우 검증"""
        if not v or not v.strip():
            raise ValueError("필드는 비어있을 수 없습니다.")
        return v.strip()


# 3. 응답 모델 (Read/Create/Update 응답)
class VocabularyResponse(VocabularyBase):
    wb_id: int
    date: date  # DB에서 DATE 타입으로 받기 때문에 date 객체로 변환
    created_at: datetime
    updated_at: datetime

    # ORM 모드 활성화 (DB 딕셔너리 결과와 매핑)
    class Config:
        from_attributes = True
        # DB 컬럼명과 모델 필드명 매핑
        populate_by_name = True

    # DB 컬럼명(WB_ID, WORD_ENGLISH, WORD_MEANING)과 모델 필드명(id, english_word, korean_meaning) 매핑을 위한 커스텀 생성자
    @classmethod
    def from_db_dict(cls, db_dict: dict):
        """데이터베이스 딕셔너리를 VocabularyResponse 객체로 변환"""
        return cls(
            wb_id=db_dict.get("WB_ID"),
            english_word=db_dict.get("WORD_ENGLISH"),
            korean_meaning=db_dict.get("WORD_MEANING"),
            source_url=db_dict.get("SOURCE_URL"),
            date=db_dict.get("DATE"),
            created_at=db_dict.get("CREATED_AT"),
            updated_at=db_dict.get("UPDATED_AT"),
        )


# 4. 날짜별 단어 목록 응답 모델 (날짜 + source_url + 단어 목록)
class VocabularyListResponse(BaseModel):
    date: str  # YYYY-MM-DD
    source_url: Optional[str] = (
        None  # 해당 날짜의 대표 source_url (null이 아닌 값 중 하나)
    )
    words: List[VocabularyResponse]  # 단어 목록

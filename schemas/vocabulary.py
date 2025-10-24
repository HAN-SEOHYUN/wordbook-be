from pydantic import BaseModel, field_validator
from datetime import datetime, date
from typing import Optional


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
    english_word: str
    korean_meaning: str
    source_url: Optional[str] = None


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
    english_word: str
    korean_meaning: str


# 3. 응답 모델 (Read/Create/Update 응답)
class VocabularyResponse(VocabularyBase):
    id: int
    date: date  # DB에서 DATE 타입으로 받기 때문에 date 객체로 변환
    created_at: datetime
    updated_at: datetime

    # ORM 모드 활성화 (DB 딕셔너리 결과와 매핑)
    class Config:
        from_attributes = True

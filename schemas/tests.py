from pydantic import BaseModel, field_validator
from datetime import datetime, date
from typing import Optional, List

# 시험 시작 요청
class TestStartRequest(BaseModel):
    u_id: int
    twi_id: int

    @field_validator("u_id", "twi_id")
    @classmethod
    def check_positive(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("ID must be positive")
        return v

# 시험 시작 응답
class TestStartResponse(BaseModel):
    tr_id: int
    u_id: int
    twi_id: int
    test_score: Optional[int]
    status: str  # "created" or "retry"
    message: str
    previous_score: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# 답안 항목
class AnswerItem(BaseModel):
    tw_id: int
    user_answer: str

    @field_validator("tw_id")
    @classmethod
    def check_positive_tw_id(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("tw_id must be positive")
        return v

    @field_validator("user_answer")
    @classmethod
    def normalize_answer(cls, v: str) -> str:
        # 빈 답안 허용 (strip만 수행)
        return v.strip() if v else ""

# 답안 제출 요청
class TestSubmitRequest(BaseModel):
    answers: list[AnswerItem]

    @field_validator("answers")
    @classmethod
    def check_answers_not_empty(cls, v: list) -> list:
        if not v:
            raise ValueError("answers cannot be empty")
        return v

# 답안 결과 항목
class AnswerResultItem(BaseModel):
    ta_id: int
    tw_id: int
    word_english: str
    word_meaning: str
    user_answer: str
    is_correct: bool

# 답안 제출 응답
class TestSubmitResponse(BaseModel):
    tr_id: int
    test_score: int
    total_questions: int
    correct_count: int
    incorrect_count: int
    results: list[AnswerResultItem]

# 시험 가능 여부 확인 응답 - 시험 주차 정보
class TestAvailabilityWeekInfo(BaseModel):
    twi_id: int
    name: str
    start_date: date
    end_date: date
    test_start_datetime: datetime
    test_end_datetime: datetime

# 시험 가능 여부 확인 응답
class TestAvailabilityResponse(BaseModel):
    is_available: bool
    test_week: Optional[TestAvailabilityWeekInfo] = None
    remaining_minutes: Optional[int] = None
    next_test_datetime: Optional[datetime] = None


# ============================================================
# 시험 기록 관련 스키마
# ============================================================

# 시험 기록 항목
class TestHistoryItem(BaseModel):
    tr_id: int
    u_id: int
    twi_id: int
    test_score: int
    created_at: datetime
    updated_at: datetime
    week_name: str
    start_date: date
    end_date: date
    test_date: date
    total_questions: int
    correct_count: int

    class Config:
        from_attributes = True


# 시험 기록 히스토리 응답
class TestHistoryResponse(BaseModel):
    user_id: int
    username: str
    test_history: List[TestHistoryItem]


# 시험 상세 답안 항목
class TestAnswerDetail(BaseModel):
    ta_id: int
    tw_id: int
    word_english: str
    word_meaning: str
    user_answer: str
    is_correct: bool

    class Config:
        from_attributes = True


# 시험 상세 결과 응답
class TestDetailResponse(BaseModel):
    tr_id: int
    u_id: int
    username: str
    twi_id: int
    week_name: str
    test_score: int
    test_date: datetime
    total_questions: int
    correct_count: int
    answers: List[TestAnswerDetail]

    class Config:
        from_attributes = True

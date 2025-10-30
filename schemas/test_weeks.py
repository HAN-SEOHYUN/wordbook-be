from pydantic import BaseModel
from datetime import date, datetime

# 주차 정보 응답 모델
class TestWeekResponse(BaseModel):
    twi_id: int
    name: str
    start_date: date
    end_date: date
    test_start_datetime: datetime
    test_end_datetime: datetime
    word_count: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# 주차 목록 응답 모델
class TestWeekListResponse(BaseModel):
    weeks: list[TestWeekResponse]

# 주차별 단어 응답 모델
class TestWeekWordResponse(BaseModel):
    tw_id: int
    wb_id: int
    word_english: str
    word_meaning: str
    date: date

    class Config:
        from_attributes = True

# 주차별 단어 목록 응답 모델
class TestWeekWordsResponse(BaseModel):
    twi_id: int
    week_name: str
    start_date: date
    end_date: date
    test_start_datetime: datetime
    test_end_datetime: datetime
    words: list[TestWeekWordResponse]

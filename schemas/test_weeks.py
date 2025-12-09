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

    # DB 컬럼명과 모델 필드명 매핑을 위한 커스텀 생성자
    @classmethod
    def from_db_dict(cls, db_dict: dict):
        """데이터베이스 딕셔너리를 TestWeekResponse 객체로 변환"""
        return cls(
            twi_id=db_dict.get("TWI_ID"),
            name=db_dict.get("NAME"),
            start_date=db_dict.get("START_DATE"),
            end_date=db_dict.get("END_DATE"),
            test_start_datetime=db_dict.get("TEST_START_DATETIME"),
            test_end_datetime=db_dict.get("TEST_END_DATETIME"),
            word_count=db_dict.get("word_count") or db_dict.get("WORD_COUNT") or 0,  # COUNT 결과는 소문자 또는 대문자일 수 있음
            created_at=db_dict.get("CREATED_AT"),
            updated_at=db_dict.get("UPDATED_AT"),
        )

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

    # DB 컬럼명과 모델 필드명 매핑을 위한 커스텀 생성자
    @classmethod
    def from_db_dict(cls, db_dict: dict):
        """데이터베이스 딕셔너리를 TestWeekWordResponse 객체로 변환"""
        return cls(
            tw_id=db_dict.get("TW_ID"),
            wb_id=db_dict.get("WB_ID"),
            word_english=db_dict.get("WORD_ENGLISH"),
            word_meaning=db_dict.get("WORD_MEANING"),
            date=db_dict.get("DATE"),
        )

# 주차별 단어 목록 응답 모델
class TestWeekWordsResponse(BaseModel):
    twi_id: int
    week_name: str
    start_date: date
    end_date: date
    test_start_datetime: datetime
    test_end_datetime: datetime
    words: list[TestWeekWordResponse]

from fastapi import APIRouter, Depends, Query
from core.database import DatabaseManager
from services.test_weeks import TestWeekService
from schemas.test_weeks import TestWeekListResponse, TestWeekWordsResponse

router = APIRouter(
    prefix="/test-weeks",
    tags=["Test Week Management"],
)


def get_db_manager() -> DatabaseManager:
    """DatabaseManager 인스턴스를 생성하고 제공합니다."""
    return DatabaseManager()


def get_test_week_service(
    db_manager: DatabaseManager = Depends(get_db_manager),
) -> TestWeekService:
    """TestWeekService 인스턴스를 생성하고 제공합니다."""
    return TestWeekService(db_manager)


@router.get(
    "/",
    response_model=TestWeekListResponse,
    summary="Get All Test Weeks",
)
def get_test_weeks(
    limit: int = Query(10, ge=1, le=50, description="Maximum number of weeks to return"),
    order: str = Query("desc", pattern="^(desc|asc)$", description="Sort order (desc=newest first, asc=oldest first)"),
    service: TestWeekService = Depends(get_test_week_service),
):
    """
    시험 주차 목록을 조회합니다.
    """
    return service.get_all_test_weeks(limit, order)


@router.get(
    "/{twi_id}/words",
    response_model=TestWeekWordsResponse,
    summary="Get Words for a Specific Test Week",
)
def get_test_week_words(
    twi_id: int,
    service: TestWeekService = Depends(get_test_week_service),
):
    """
    특정 주차의 단어 목록을 조회합니다.
    """
    return service.get_test_week_words(twi_id)

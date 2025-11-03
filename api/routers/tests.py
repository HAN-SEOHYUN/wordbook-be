from fastapi import APIRouter, Depends, status
from core.database import DatabaseManager
from services.tests import TestService
from schemas.tests import (
    TestStartRequest,
    TestStartResponse,
    TestSubmitRequest,
    TestSubmitResponse,
    TestAvailabilityResponse,
    TestHistoryResponse,
    TestDetailResponse,
)

router = APIRouter(
    prefix="/tests",
    tags=["Test Management"],
)


def get_db_manager() -> DatabaseManager:
    """DatabaseManager 인스턴스를 생성하고 제공합니다."""
    return DatabaseManager()


def get_test_service(
    db_manager: DatabaseManager = Depends(get_db_manager),
) -> TestService:
    """TestService 인스턴스를 생성하고 제공합니다."""
    return TestService(db_manager)


@router.post(
    "/start",
    response_model=TestStartResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Start a New Test",
)
def start_test(
    request: TestStartRequest,
    service: TestService = Depends(get_test_service),
):
    """
    시험을 시작합니다. 이미 시험 기록이 있으면 재시험으로 처리됩니다.
    """
    return service.start_test(request)


@router.post(
    "/{tr_id}/submit",
    response_model=TestSubmitResponse,
    summary="Submit Test Answers and Get Results",
)
def submit_test(
    tr_id: int,
    request: TestSubmitRequest,
    service: TestService = Depends(get_test_service),
):
    """
    답안을 제출하고 자동 채점 결과를 받습니다.
    """
    return service.submit_test(tr_id, request)


@router.get(
    "/current-availability",
    response_model=TestAvailabilityResponse,
    summary="Check Current Test Availability",
)
def get_current_availability(
    service: TestService = Depends(get_test_service),
):
    """
    현재 시험 가능 여부를 확인합니다.
    시험 시간(토요일 10:10~10:25) 내라면 is_available=True를 반환합니다.
    """
    return service.get_current_availability()


@router.get(
    "/history",
    response_model=TestHistoryResponse,
    summary="Get Test History for a User",
)
def get_test_history(
    u_id: int,
    service: TestService = Depends(get_test_service),
):
    """
    사용자의 시험 기록 히스토리를 조회합니다.
    완료된 시험(test_score가 NULL이 아닌)만 반환됩니다.
    """
    return service.get_test_history(u_id)


@router.get(
    "/{tr_id}/detail",
    response_model=TestDetailResponse,
    summary="Get Detailed Test Results",
)
def get_test_detail(
    tr_id: int,
    service: TestService = Depends(get_test_service),
):
    """
    특정 시험의 상세 결과를 조회합니다.
    시험 기본 정보와 각 문항별 답안을 포함합니다.
    """
    return service.get_test_detail(tr_id)

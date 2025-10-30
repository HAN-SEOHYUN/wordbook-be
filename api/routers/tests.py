from fastapi import APIRouter, Depends, status
from core.database import DatabaseManager
from services.tests import TestService
from schemas.tests import (
    TestStartRequest,
    TestStartResponse,
    TestSubmitRequest,
    TestSubmitResponse,
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

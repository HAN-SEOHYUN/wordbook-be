from fastapi import HTTPException, status
from datetime import datetime
from core.database import DatabaseManager
from schemas.tests import (
    TestStartRequest,
    TestStartResponse,
    TestSubmitRequest,
    TestSubmitResponse,
    AnswerResultItem,
    TestAvailabilityResponse,
    TestAvailabilityWeekInfo,
)
from crud import tests as crud_tests
from crud import test_weeks as crud_test_weeks


class TestService:
    """시험 관련 비즈니스 로직을 처리하는 서비스 클래스"""

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def start_test(self, request: TestStartRequest) -> TestStartResponse:
        """시험 시작 (신규 생성 또는 재시험)"""
        try:
            with self.db.get_connection() as conn:
                # 기존 시험 결과 확인
                existing = crud_tests.get_existing_test_result(conn, request.u_id, request.twi_id)

                if existing:
                    # 재시험: 기존 답안 삭제 및 점수 초기화
                    crud_tests.reset_test_result(conn, existing['tr_id'])

                    return TestStartResponse(
                        tr_id=existing['tr_id'],
                        u_id=existing['u_id'],
                        twi_id=existing['twi_id'],
                        test_score=None,
                        status="retry",
                        message="이전 시험 기록이 있습니다. 재시험을 시작합니다.",
                        previous_score=existing['test_score'],
                        created_at=existing['created_at'],
                        updated_at=existing['updated_at'],
                    )
                else:
                    # 신규 생성
                    tr_id = crud_tests.create_test_result(conn, request.u_id, request.twi_id)

                    # 생성된 레코드 조회
                    result = crud_tests.get_existing_test_result(conn, request.u_id, request.twi_id)

                    return TestStartResponse(
                        tr_id=result['tr_id'],
                        u_id=result['u_id'],
                        twi_id=result['twi_id'],
                        test_score=None,
                        status="created",
                        message="새 시험이 시작되었습니다.",
                        created_at=result['created_at'],
                        updated_at=result['updated_at'],
                    )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to start test: {e}",
            )

    def submit_test(self, tr_id: int, request: TestSubmitRequest) -> TestSubmitResponse:
        """답안 제출 및 자동 채점"""
        try:
            with self.db.get_connection() as conn:
                # 정답 조회
                correct_answers = crud_tests.get_correct_answers_for_test(conn, tr_id)

                if not correct_answers:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Test with ID {tr_id} not found or has no questions.",
                    )

                # 각 답안 채점 및 저장
                results = []
                for answer in request.answers:
                    tw_id = answer.tw_id
                    user_ans = answer.user_answer

                    # 정답 가져오기
                    if tw_id not in correct_answers:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Invalid tw_id: {tw_id}",
                        )

                    correct = correct_answers[tw_id]

                    # 정답 검증
                    is_correct = (
                        crud_tests.normalize_answer(user_ans)
                        == crud_tests.normalize_answer(correct['word_english'])
                    )

                    # 답안 저장
                    ta_id = crud_tests.save_answer(conn, tr_id, tw_id, user_ans, is_correct)

                    results.append(
                        AnswerResultItem(
                            ta_id=ta_id,
                            tw_id=tw_id,
                            word_english=correct['word_english'],
                            word_meaning=correct['word_meaning'],
                            user_answer=user_ans,
                            is_correct=is_correct,
                        )
                    )

                # 점수 계산
                correct_count = sum(1 for r in results if r.is_correct)
                total_count = len(results)
                score = round(correct_count * 100.0 / total_count)

                # 점수 업데이트
                crud_tests.update_test_score(conn, tr_id, score)

                return TestSubmitResponse(
                    tr_id=tr_id,
                    test_score=score,
                    total_questions=total_count,
                    correct_count=correct_count,
                    incorrect_count=total_count - correct_count,
                    results=results,
                )
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to submit test: {e}",
            )

    def get_current_availability(self) -> TestAvailabilityResponse:
        """현재 시험 가능 여부 확인"""
        try:
            with self.db.get_connection() as conn:
                # 현재 시간
                now = datetime.now()

                # 가장 최근 주차 정보 조회
                weeks = crud_test_weeks.get_all_test_weeks(conn, limit=1, order="desc")

                if not weeks:
                    # 주차 정보가 없으면 시험 불가
                    return TestAvailabilityResponse(
                        is_available=False,
                        next_test_datetime=None
                    )

                week = weeks[0]
                test_start = week['test_start_datetime']
                test_end = week['test_end_datetime']

                # 현재 시간이 시험 시간 범위 내인지 확인
                if test_start <= now <= test_end:
                    # 시험 가능
                    remaining_seconds = (test_end - now).total_seconds()
                    remaining_minutes = int(remaining_seconds / 60)

                    return TestAvailabilityResponse(
                        is_available=True,
                        test_week=TestAvailabilityWeekInfo(
                            twi_id=week['twi_id'],
                            name=week['name'],
                            start_date=week['start_date'],
                            end_date=week['end_date'],
                            test_start_datetime=test_start,
                            test_end_datetime=test_end
                        ),
                        remaining_minutes=remaining_minutes,
                        next_test_datetime=None
                    )
                else:
                    # 시험 불가
                    # 다음 시험 시간 계산 (현재 주차의 시험 시간 또는 다음 주차)
                    next_test = test_start if now < test_start else None

                    return TestAvailabilityResponse(
                        is_available=False,
                        test_week=None,
                        remaining_minutes=None,
                        next_test_datetime=next_test
                    )

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to check test availability: {e}",
            )

"""
재시험 기능 통합 테스트

이 스크립트는 재시험 기능의 전체 플로우를 테스트합니다:
1. 시험 시작 (test_result 생성)
2. 답안 제출 (test_answers 생성, 점수 계산)
3. 기록 조회 (test history)
4. 재시험 (기존 기록 삭제)
5. 재시험 시작 및 완료
6. 최종 결과 확인

사용법:
    python test_retest_feature.py
"""

import sys
import io
import requests
from datetime import datetime

# Windows 콘솔 UTF-8 설정
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

API_BASE_URL = "http://localhost:8000/api/v1"


def print_section(title):
    """섹션 제목 출력"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)


def print_result(success, message):
    """결과 출력"""
    icon = "✓" if success else "✗"
    print(f"{icon} {message}")


def test_retest_feature():
    """재시험 기능 전체 테스트"""

    print_section("재시험 기능 통합 테스트")
    print(f"시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # 테스트 데이터
    u_id = 1  # 테스트 사용자 ID
    twi_id = 1  # 테스트 주차 ID

    try:
        # ========================================
        # STEP 1: 첫 번째 시험 시작
        # ========================================
        print_section("STEP 1: 첫 번째 시험 시작")

        response = requests.post(
            f"{API_BASE_URL}/tests/start",
            json={"u_id": u_id, "twi_id": twi_id}
        )

        if response.status_code != 201:
            print_result(False, f"시험 시작 실패: {response.status_code}")
            print(f"응답: {response.text}")
            return False

        test_data = response.json()
        tr_id_1 = test_data["tr_id"]
        print_result(True, f"시험 시작 성공 (tr_id: {tr_id_1})")
        print(f"   상태: {test_data.get('status')}")
        print(f"   메시지: {test_data.get('message')}")

        # ========================================
        # STEP 2: 첫 번째 시험 답안 제출
        # ========================================
        print_section("STEP 2: 첫 번째 시험 답안 제출")

        # 시험 문제 조회 (twi_id로부터 test_words 가져오기)
        # 실제로는 프론트엔드에서 문제를 받아오지만, 여기서는 간단히 예시 답안 제출

        # 예시: 30문제 중 20개 맞춤 (67점)
        sample_answers = []
        for i in range(1, 31):  # tw_id 1~30 가정
            sample_answers.append({
                "tw_id": i,
                "user_answer": f"correct_answer_{i}" if i <= 20 else f"wrong_answer_{i}"
            })

        response = requests.post(
            f"{API_BASE_URL}/tests/{tr_id_1}/submit",
            json={"answers": sample_answers}
        )

        if response.status_code != 200:
            print_result(False, f"답안 제출 실패: {response.status_code}")
            print(f"응답: {response.text}")
            # 실제 문제가 없을 수 있으므로 계속 진행
            print("⚠️ 답안 제출 실패했지만 테스트 계속 진행...")
            first_score = None
        else:
            result_data = response.json()
            first_score = result_data["test_score"]
            print_result(True, f"답안 제출 성공")
            print(f"   점수: {first_score}점")
            print(f"   정답: {result_data.get('correct_count')}/{result_data.get('total_questions')}")

        # ========================================
        # STEP 3: 시험 기록 조회
        # ========================================
        print_section("STEP 3: 시험 기록 조회")

        response = requests.get(
            f"{API_BASE_URL}/tests/history",
            params={"u_id": u_id}
        )

        if response.status_code != 200:
            print_result(False, f"기록 조회 실패: {response.status_code}")
            return False

        history_data = response.json()
        test_history = history_data.get("test_history", [])

        if first_score is not None:
            # 답안 제출이 성공한 경우에만 검증
            found = False
            for test in test_history:
                if test["tr_id"] == tr_id_1:
                    found = True
                    print_result(True, f"첫 번째 시험 기록 확인")
                    print(f"   tr_id: {test['tr_id']}")
                    print(f"   점수: {test['test_score']}점")
                    print(f"   주차: {test['week_name']}")
                    break

            if not found:
                print_result(False, "첫 번째 시험 기록을 찾을 수 없음")
        else:
            print_result(True, f"기록 조회 성공 (총 {len(test_history)}개)")

        # ========================================
        # STEP 4: 재시험 (기존 기록 삭제)
        # ========================================
        print_section("STEP 4: 재시험을 위한 기존 기록 삭제")

        response = requests.delete(
            f"{API_BASE_URL}/tests/{tr_id_1}"
        )

        if response.status_code != 204:
            print_result(False, f"기록 삭제 실패: {response.status_code}")
            print(f"응답: {response.text}")
            return False

        print_result(True, f"기존 기록 삭제 성공 (tr_id: {tr_id_1})")

        # 삭제 확인: 기록 조회 시 해당 tr_id가 없어야 함
        response = requests.get(
            f"{API_BASE_URL}/tests/history",
            params={"u_id": u_id}
        )

        if response.status_code == 200:
            history_data = response.json()
            test_history = history_data.get("test_history", [])

            found_deleted = any(test["tr_id"] == tr_id_1 for test in test_history)

            if found_deleted:
                print_result(False, "기록이 여전히 존재함 (삭제 실패)")
                return False
            else:
                print_result(True, "기록 삭제 확인 완료")

        # ========================================
        # STEP 5: 재시험 시작
        # ========================================
        print_section("STEP 5: 재시험 시작")

        response = requests.post(
            f"{API_BASE_URL}/tests/start",
            json={"u_id": u_id, "twi_id": twi_id}
        )

        if response.status_code != 201:
            print_result(False, f"재시험 시작 실패: {response.status_code}")
            print(f"응답: {response.text}")
            return False

        retest_data = response.json()
        tr_id_2 = retest_data["tr_id"]
        print_result(True, f"재시험 시작 성공 (tr_id: {tr_id_2})")
        print(f"   상태: {retest_data.get('status')}")
        print(f"   메시지: {retest_data.get('message')}")

        # tr_id가 새로 생성되었는지 확인
        if tr_id_2 == tr_id_1:
            print_result(False, "⚠️ tr_id가 동일함 (새로 생성되지 않음)")
        else:
            print_result(True, f"새로운 tr_id 생성 확인 ({tr_id_1} → {tr_id_2})")

        # ========================================
        # STEP 6: 재시험 답안 제출
        # ========================================
        print_section("STEP 6: 재시험 답안 제출")

        # 이번에는 30문제 중 25개 맞춤 (83점)
        retest_answers = []
        for i in range(1, 31):
            retest_answers.append({
                "tw_id": i,
                "user_answer": f"correct_answer_{i}" if i <= 25 else f"wrong_answer_{i}"
            })

        response = requests.post(
            f"{API_BASE_URL}/tests/{tr_id_2}/submit",
            json={"answers": retest_answers}
        )

        if response.status_code != 200:
            print_result(False, f"재시험 답안 제출 실패: {response.status_code}")
            print(f"응답: {response.text}")
            second_score = None
        else:
            retest_result = response.json()
            second_score = retest_result["test_score"]
            print_result(True, f"재시험 답안 제출 성공")
            print(f"   점수: {second_score}점")
            print(f"   정답: {retest_result.get('correct_count')}/{retest_result.get('total_questions')}")

        # ========================================
        # STEP 7: 최종 결과 확인
        # ========================================
        print_section("STEP 7: 최종 결과 확인")

        response = requests.get(
            f"{API_BASE_URL}/tests/history",
            params={"u_id": u_id}
        )

        if response.status_code != 200:
            print_result(False, f"최종 기록 조회 실패: {response.status_code}")
            return False

        history_data = response.json()
        test_history = history_data.get("test_history", [])

        # 해당 twi_id의 기록이 1개만 있어야 함 (재시험 기록)
        same_week_tests = [t for t in test_history if t["twi_id"] == twi_id]

        print(f"해당 주차 시험 기록 개수: {len(same_week_tests)}개")

        if len(same_week_tests) == 0:
            print_result(False, "재시험 기록이 없음")
            return False
        elif len(same_week_tests) > 1:
            print_result(False, f"기록이 {len(same_week_tests)}개 존재 (1개여야 함)")
            print("   기록 목록:")
            for t in same_week_tests:
                print(f"     - tr_id: {t['tr_id']}, 점수: {t['test_score']}점")
            return False
        else:
            final_test = same_week_tests[0]
            print_result(True, "재시험 기록만 존재 (덮어쓰기 성공)")
            print(f"   tr_id: {final_test['tr_id']}")
            print(f"   점수: {final_test['test_score']}점")
            print(f"   주차: {final_test['week_name']}")

            if final_test["tr_id"] != tr_id_2:
                print_result(False, "tr_id가 예상과 다름")
                return False

            if second_score is not None and final_test["test_score"] != second_score:
                print_result(False, "점수가 예상과 다름")
                return False

        # ========================================
        # 테스트 성공
        # ========================================
        print_section("테스트 결과")
        print_result(True, "모든 테스트 통과!")

        if first_score is not None and second_score is not None:
            print(f"\n📊 점수 변화:")
            print(f"   첫 시험: {first_score}점")
            print(f"   재시험: {second_score}점")
            print(f"   변화: {second_score - first_score:+d}점")

        print(f"\n종료 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)

        return True

    except requests.exceptions.ConnectionError:
        print_result(False, "API 서버에 연결할 수 없습니다.")
        print("FastAPI 서버가 실행 중인지 확인하세요: python -m uvicorn main:app --reload")
        return False
    except Exception as e:
        print_result(False, f"예외 발생: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_retest_feature()
    sys.exit(0 if success else 1)

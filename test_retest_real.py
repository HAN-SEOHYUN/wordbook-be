"""
실제 데이터로 재시험 기능 테스트

이 스크립트는 DB에 실제로 존재하는 데이터를 사용해서 재시험 기능을 테스트합니다.
먼저 check_test_data.py를 실행해서 사용 가능한 데이터를 확인하세요.

사용법:
    python test_retest_real.py
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


def test_retest_with_real_data():
    """실제 데이터로 재시험 기능 테스트"""

    print_section("실제 데이터로 재시험 기능 테스트")
    print(f"시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # 실제 DB 데이터 사용
    # check_test_data.py 결과를 참고하여 설정
    u_id = 2  # 상로
    twi_id = 3  # 11월 1주차 (문제 30개 존재)

    print(f"\n테스트 데이터:")
    print(f"  u_id: {u_id}")
    print(f"  twi_id: {twi_id}")

    try:
        # ========================================
        # STEP 1: 기존 시험 기록 확인
        # ========================================
        print_section("STEP 1: 기존 시험 기록 확인")

        response = requests.get(
            f"{API_BASE_URL}/tests/history",
            params={"u_id": u_id}
        )

        if response.status_code != 200:
            print_result(False, f"기록 조회 실패: {response.status_code}")
            return False

        history_data = response.json()
        test_history = history_data.get("test_history", [])

        # 해당 twi_id의 기록 찾기
        existing_test = None
        for test in test_history:
            if test["twi_id"] == twi_id:
                existing_test = test
                break

        if existing_test:
            print_result(True, "기존 시험 기록 발견")
            print(f"   tr_id: {existing_test['tr_id']}")
            print(f"   점수: {existing_test['test_score']}점")
            print(f"   주차: {existing_test['week_name']}")
            tr_id_before = existing_test['tr_id']
            score_before = existing_test['test_score']
        else:
            print_result(True, "기존 시험 기록 없음 (새로운 시험)")
            tr_id_before = None
            score_before = None

        # ========================================
        # STEP 2: 재시험 - 기존 기록 삭제 (있는 경우)
        # ========================================
        if tr_id_before:
            print_section("STEP 2: 기존 기록 삭제 (재시험 준비)")

            response = requests.delete(
                f"{API_BASE_URL}/tests/{tr_id_before}"
            )

            if response.status_code != 204:
                print_result(False, f"기록 삭제 실패: {response.status_code}")
                print(f"응답: {response.text}")
                return False

            print_result(True, f"기존 기록 삭제 성공 (tr_id: {tr_id_before})")

            # 삭제 확인
            response = requests.get(
                f"{API_BASE_URL}/tests/history",
                params={"u_id": u_id}
            )

            if response.status_code == 200:
                history_data = response.json()
                test_history = history_data.get("test_history", [])

                found_deleted = any(test["tr_id"] == tr_id_before for test in test_history)

                if found_deleted:
                    print_result(False, "기록이 여전히 존재함 (삭제 실패)")
                    return False
                else:
                    print_result(True, "기록 삭제 확인 완료")

        # ========================================
        # STEP 3: 시험 시작
        # ========================================
        print_section("STEP 3: 시험 시작")

        response = requests.post(
            f"{API_BASE_URL}/tests/start",
            json={"u_id": u_id, "twi_id": twi_id}
        )

        if response.status_code != 201:
            print_result(False, f"시험 시작 실패: {response.status_code}")
            print(f"응답: {response.text}")
            return False

        test_data = response.json()
        tr_id_new = test_data["tr_id"]
        print_result(True, f"시험 시작 성공 (tr_id: {tr_id_new})")
        print(f"   상태: {test_data.get('status')}")
        print(f"   메시지: {test_data.get('message')}")

        if tr_id_before:
            if tr_id_new == tr_id_before:
                print_result(False, "⚠️ tr_id가 동일함 (새로 생성되지 않음)")
            else:
                print_result(True, f"새로운 tr_id 생성 확인 ({tr_id_before} → {tr_id_new})")

        # ========================================
        # STEP 4: 시험 문제 조회
        # ========================================
        print_section("STEP 4: 시험 문제 조회")

        # test_words 조회하여 실제 문제 확인
        from core.database import DatabaseManager
        db = DatabaseManager()

        with db.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT tw.tw_id, wb.word_english, wb.word_meaning
                    FROM test_words tw
                    JOIN word_book wb ON tw.wb_id = wb.wb_id
                    WHERE tw.twi_id = %s
                    LIMIT 5
                """, (twi_id,))
                questions = cursor.fetchall()

                if questions:
                    print_result(True, f"시험 문제 조회 성공 (총 {len(questions)}개 중 5개 표시)")
                    for i, q in enumerate(questions, 1):
                        print(f"   {i}. tw_id: {q['tw_id']}, {q['word_meaning']} = {q['word_english']}")
                else:
                    print_result(False, "시험 문제가 없음")
                    return False

        # ========================================
        # STEP 5: 답안 제출 (실제 정답 사용)
        # ========================================
        print_section("STEP 5: 답안 제출")

        # 모든 문제의 정답을 가져와서 일부만 맞추기
        with db.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT tw.tw_id, wb.word_english
                    FROM test_words tw
                    JOIN word_book wb ON tw.wb_id = wb.wb_id
                    WHERE tw.twi_id = %s
                """, (twi_id,))
                all_questions = cursor.fetchall()

        # 80% 정답 (24/30)
        answers = []
        for i, q in enumerate(all_questions):
            if i < len(all_questions) * 0.8:  # 80% 정답
                answers.append({
                    "tw_id": q['tw_id'],
                    "user_answer": q['word_english']  # 정답
                })
            else:
                answers.append({
                    "tw_id": q['tw_id'],
                    "user_answer": "wrong_answer"  # 오답
                })

        response = requests.post(
            f"{API_BASE_URL}/tests/{tr_id_new}/submit",
            json={"answers": answers}
        )

        if response.status_code != 200:
            print_result(False, f"답안 제출 실패: {response.status_code}")
            print(f"응답: {response.text}")
            return False

        result_data = response.json()
        score_new = result_data["test_score"]
        print_result(True, "답안 제출 성공")
        print(f"   점수: {score_new}점")
        print(f"   정답: {result_data.get('correct_count')}/{result_data.get('total_questions')}")

        # ========================================
        # STEP 6: 최종 결과 확인
        # ========================================
        print_section("STEP 6: 최종 결과 확인")

        response = requests.get(
            f"{API_BASE_URL}/tests/history",
            params={"u_id": u_id}
        )

        if response.status_code != 200:
            print_result(False, f"최종 기록 조회 실패: {response.status_code}")
            return False

        history_data = response.json()
        test_history = history_data.get("test_history", [])

        # 해당 twi_id의 기록이 1개만 있어야 함
        same_week_tests = [t for t in test_history if t["twi_id"] == twi_id]

        print(f"해당 주차 시험 기록 개수: {len(same_week_tests)}개")

        if len(same_week_tests) == 0:
            print_result(False, "시험 기록이 없음")
            return False
        elif len(same_week_tests) > 1:
            print_result(False, f"기록이 {len(same_week_tests)}개 존재 (1개여야 함)")
            for t in same_week_tests:
                print(f"     - tr_id: {t['tr_id']}, 점수: {t['test_score']}점")
            return False
        else:
            final_test = same_week_tests[0]
            print_result(True, "시험 기록 확인 완료")
            print(f"   tr_id: {final_test['tr_id']}")
            print(f"   점수: {final_test['test_score']}점")
            print(f"   주차: {final_test['week_name']}")

        # ========================================
        # 테스트 성공
        # ========================================
        print_section("테스트 결과")
        print_result(True, "모든 테스트 통과!")

        if score_before is not None:
            print(f"\n📊 점수 변화:")
            print(f"   이전 점수: {score_before}점")
            print(f"   새 점수: {score_new}점")
            print(f"   변화: {score_new - score_before:+d}점")
        else:
            print(f"\n📊 첫 시험 점수: {score_new}점")

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
    success = test_retest_with_real_data()
    sys.exit(0 if success else 1)

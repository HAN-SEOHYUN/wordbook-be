"""
DB에 존재하는 테스트 데이터 확인

사용법:
    python check_test_data.py
"""

import sys
import io
from core.database import DatabaseManager

# Windows 콘솔 UTF-8 설정
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


def check_test_data():
    """테스트에 필요한 데이터 확인"""
    db = DatabaseManager()

    print("=" * 80)
    print("테스트 데이터 확인")
    print("=" * 80)

    try:
        with db.get_connection() as conn:
            # 1. 사용자 확인
            print("\n[1] 사용자 목록 (users)")
            print("-" * 80)
            with conn.cursor() as cursor:
                cursor.execute("SELECT u_id, username, created_at FROM users ORDER BY u_id LIMIT 5")
                users = cursor.fetchall()

                if users:
                    for user in users:
                        print(f"  u_id: {user['u_id']}, username: {user['username']}")
                else:
                    print("  ⚠️ 사용자가 없습니다.")

            # 2. 주차 정보 확인
            print("\n[2] 시험 주차 정보 (test_week_info)")
            print("-" * 80)
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT twi_id, name, start_date, end_date,
                           DATE(test_start_datetime) as test_date
                    FROM test_week_info
                    ORDER BY twi_id DESC
                    LIMIT 5
                """)
                weeks = cursor.fetchall()

                if weeks:
                    for week in weeks:
                        print(f"  twi_id: {week['twi_id']}, name: {week['name']}, test_date: {week['test_date']}")
                else:
                    print("  ⚠️ 주차 정보가 없습니다.")

            # 3. 시험 문제 확인
            print("\n[3] 시험 문제 개수 (test_words)")
            print("-" * 80)
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT twi_id, COUNT(*) as word_count
                    FROM test_words
                    GROUP BY twi_id
                    ORDER BY twi_id DESC
                    LIMIT 5
                """)
                word_counts = cursor.fetchall()

                if word_counts:
                    for wc in word_counts:
                        print(f"  twi_id: {wc['twi_id']}, 문제 수: {wc['word_count']}개")
                else:
                    print("  ⚠️ 시험 문제가 없습니다.")

            # 4. 기존 시험 기록 확인
            print("\n[4] 기존 시험 기록 (test_result)")
            print("-" * 80)
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT tr_id, u_id, twi_id, test_score, created_at
                    FROM test_result
                    ORDER BY tr_id DESC
                    LIMIT 5
                """)
                results = cursor.fetchall()

                if results:
                    for result in results:
                        score = result['test_score'] if result['test_score'] is not None else "미완료"
                        print(f"  tr_id: {result['tr_id']}, u_id: {result['u_id']}, twi_id: {result['twi_id']}, 점수: {score}")
                else:
                    print("  ⚠️ 시험 기록이 없습니다.")

            # 5. 추천 테스트 데이터
            print("\n[5] 추천 테스트 데이터")
            print("-" * 80)

            if users and weeks:
                recommended_u_id = users[0]['u_id']
                recommended_twi_id = weeks[0]['twi_id']

                print(f"  ✅ 테스트에 사용할 데이터:")
                print(f"     u_id = {recommended_u_id}")
                print(f"     twi_id = {recommended_twi_id}")

                # 해당 주차에 문제가 있는지 확인
                with conn.cursor() as cursor:
                    cursor.execute("""
                        SELECT COUNT(*) as count
                        FROM test_words
                        WHERE twi_id = %s
                    """, (recommended_twi_id,))
                    word_count = cursor.fetchone()['count']

                    if word_count > 0:
                        print(f"     문제 수: {word_count}개 ✓")
                    else:
                        print(f"     문제 수: 0개 ⚠️ (시험 문제를 먼저 생성하세요)")
            else:
                print("  ⚠️ 테스트 데이터가 부족합니다.")
                if not users:
                    print("     - users 테이블에 데이터를 추가하세요")
                if not weeks:
                    print("     - test_week_info 테이블에 데이터를 추가하세요")
                    print("     - 명령어: python manage_test.py --create-week-info --date 2025-11-08")

        print("\n" + "=" * 80)
        print("확인 완료!")
        print("=" * 80)

    except Exception as e:
        print(f"\n❌ 에러 발생: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    check_test_data()

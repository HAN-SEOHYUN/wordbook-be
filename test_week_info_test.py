"""
test_week_creator 테스트
"""

import sys
import io
from datetime import datetime
from core.test_week_creator import TestWeekCreator

# Windows 콘솔 UTF-8 설정
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def test_calculate_week_info():
    """주차 정보 계산 테스트"""
    creator = TestWeekCreator()

    print("=" * 80)
    print("주차 정보 계산 테스트")
    print("=" * 80)

    # 테스트 케이스 1: 10월 4일 (토) → "10월 1주차"
    test_cases = [
        ("2025-10-04", "10월 1주차"),
        ("2025-10-11", "10월 2주차"),
        ("2025-10-18", "10월 3주차"),
        ("2025-10-25", "10월 4주차"),
        ("2025-11-01", "11월 1주차"),  # 중요: 11월 1일(토)는 11월 1주차
    ]

    all_passed = True

    for saturday_str, expected_name in test_cases:
        saturday = datetime.strptime(saturday_str, "%Y-%m-%d")
        name, start_date, end_date = creator.calculate_week_info(saturday)

        passed = (name == expected_name)
        status = "✓ PASS" if passed else "✗ FAIL"

        print(f"\n{status} 토요일: {saturday_str}")
        print(f"  예상: {expected_name}")
        print(f"  결과: {name}")
        print(f"  범위: {start_date} ~ {end_date}")

        if not passed:
            all_passed = False

    print("\n" + "=" * 80)
    if all_passed:
        print("✅ 모든 테스트 통과!")
    else:
        print("❌ 일부 테스트 실패")
    print("=" * 80)

    return all_passed


if __name__ == "__main__":
    test_calculate_week_info()

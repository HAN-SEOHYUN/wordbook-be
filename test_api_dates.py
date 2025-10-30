"""
/api/v1/vocabulary/dates API 테스트
"""

import sys
import io
import requests

# Windows 콘솔 UTF-8 설정
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

API_URL = "http://localhost:8000/api/v1/vocabulary/dates"


def test_dates_api():
    """날짜 API 테스트"""
    print("=" * 80)
    print("/api/v1/vocabulary/dates API 테스트")
    print("=" * 80)

    try:
        response = requests.get(API_URL)

        print(f"\n상태 코드: {response.status_code}")

        if response.status_code == 200:
            dates = response.json()
            print(f"✓ 성공!")
            print(f"\n반환된 날짜 개수: {len(dates)}개")
            print(f"\n날짜 목록 (최신순):")

            for i, date in enumerate(dates, 1):
                print(f"  {i}. {date}")

            # 예상 범위 확인
            print(f"\n예상 범위: 2025-10-23 ~ 2025-10-29")
            print(f"실제 범위: {dates[-1] if dates else 'N/A'} ~ {dates[0] if dates else 'N/A'}")

            # 범위 검증
            if dates:
                expected_dates = ["2025-10-23", "2025-10-27", "2025-10-28", "2025-10-29"]
                all_in_range = all(date in expected_dates for date in dates)

                if all_in_range:
                    print("\n✅ 모든 날짜가 이번주 시험 범위 내에 있습니다!")
                else:
                    print("\n⚠️ 범위 밖의 날짜가 포함되어 있습니다.")
                    out_of_range = [date for date in dates if date not in expected_dates]
                    print(f"범위 밖: {out_of_range}")
            else:
                print("\n⚠️ 날짜가 없습니다.")

        else:
            print(f"✗ 실패: {response.status_code}")
            print(f"응답: {response.text}")

    except requests.exceptions.ConnectionError:
        print("✗ API 서버에 연결할 수 없습니다.")
        print("FastAPI 서버가 실행 중인지 확인하세요.")
    except Exception as e:
        print(f"✗ 에러 발생: {e}")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    test_dates_api()

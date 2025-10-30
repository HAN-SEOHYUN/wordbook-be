"""
test_week_info INSERT 시 각 컬럼 값을 확인하는 테스트 코드

사용법:
    python test_week_creator_full.py 2025-11-01
    python test_week_creator_full.py 2025-11-08
"""

import sys
import os
from datetime import datetime
from core.test_week_creator import TestWeekCreator

# Windows 환경에서 UTF-8 출력 지원
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')


def test_week_info_values(date_string: str):
    """
    주어진 날짜에 대해 test_week_info에 INSERT할 값들을 출력합니다.

    Args:
        date_string: YYYY-MM-DD 형식의 날짜 문자열
    """
    print("=" * 80)
    print(f"테스트 날짜: {date_string}")
    print("=" * 80)

    try:
        # 날짜 파싱
        base_date = datetime.strptime(date_string, "%Y-%m-%d")
        print(f"✓ 입력 날짜 파싱 성공: {base_date.strftime('%Y-%m-%d %A')}")
        print()

        # TestWeekCreator 인스턴스 생성
        creator = TestWeekCreator()

        # 1. 이번주 토요일 계산
        saturday = creator.get_this_saturday(base_date)
        saturday_str = saturday.strftime("%Y-%m-%d")
        print(f"📅 이번주 토요일: {saturday_str} ({saturday.strftime('%A')})")
        print()

        # 2. 주차 정보 계산
        name, start_date, end_date, test_start_datetime, test_end_datetime = creator.calculate_week_info(saturday)

        # 3. 결과 출력
        print("=" * 80)
        print("🎯 INSERT할 값들:")
        print("=" * 80)
        print()

        print("📝 SQL INSERT 문:")
        print("-" * 80)
        print("INSERT INTO test_week_info")
        print("  (name, start_date, end_date, test_start_datetime, test_end_datetime)")
        print("VALUES")
        print(f"  ('{name}', '{start_date}', '{end_date}', '{test_start_datetime}', '{test_end_datetime}');")
        print()

        print("=" * 80)
        print("📋 각 컬럼 상세:")
        print("=" * 80)
        print()

        # name
        print(f"🏷️  name (주차명):")
        print(f"   값: {name}")
        print(f"   설명: {saturday.month}월의 {name.split()[1]} (토요일 기준)")
        print()

        # start_date
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        print(f"📆 start_date (주차 시작일):")
        print(f"   값: {start_date}")
        print(f"   요일: {start_dt.strftime('%A')}")
        print(f"   설명: 전주 목요일 (토요일 - 9일)")
        print()

        # end_date
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        print(f"📆 end_date (주차 종료일):")
        print(f"   값: {end_date}")
        print(f"   요일: {end_dt.strftime('%A')}")
        print(f"   설명: 당주 수요일 (토요일 - 3일)")
        print()

        # test_start_datetime
        test_start_dt = datetime.strptime(test_start_datetime, "%Y-%m-%d %H:%M:%S")
        print(f"⏰ test_start_datetime (시험 시작 시간):")
        print(f"   값: {test_start_datetime}")
        print(f"   요일: {test_start_dt.strftime('%A')}")
        print(f"   시간: {test_start_dt.strftime('%H:%M:%S')}")
        print(f"   설명: 토요일 10시 10분")
        print()

        # test_end_datetime
        test_end_dt = datetime.strptime(test_end_datetime, "%Y-%m-%d %H:%M:%S")
        print(f"⏰ test_end_datetime (시험 종료 시간):")
        print(f"   값: {test_end_datetime}")
        print(f"   요일: {test_end_dt.strftime('%A')}")
        print(f"   시간: {test_end_dt.strftime('%H:%M:%S')}")
        print(f"   설명: 토요일 10시 25분 (15분간)")
        print()

        # 검증
        print("=" * 80)
        print("✅ 검증:")
        print("=" * 80)
        print()

        # 요일 검증
        print("1. 요일 검증:")
        print(f"   - start_date는 목요일인가? {start_dt.strftime('%A') == 'Thursday'} ({start_dt.strftime('%A')})")
        print(f"   - end_date는 수요일인가? {end_dt.strftime('%A') == 'Wednesday'} ({end_dt.strftime('%A')})")
        print(f"   - 시험일은 토요일인가? {test_start_dt.strftime('%A') == 'Saturday'} ({test_start_dt.strftime('%A')})")
        print()

        # 날짜 범위 검증
        days_range = (end_dt - start_dt).days
        print("2. 날짜 범위 검증:")
        print(f"   - 주차 기간: {days_range}일 (목~수 = 6일이어야 함)")
        print(f"   - 검증 결과: {'✓ 정상' if days_range == 6 else '✗ 오류'}")
        print()

        # 시험 시간 검증
        print("3. 시험 시간 검증:")
        print(f"   - 시작 시간: {test_start_dt.hour}:{test_start_dt.minute:02d} (10:10이어야 함)")
        print(f"   - 종료 시간: {test_end_dt.hour}:{test_end_dt.minute:02d} (10:25이어야 함)")
        test_duration = (test_end_dt - test_start_dt).total_seconds() / 60
        print(f"   - 시험 시간: {int(test_duration)}분 (15분이어야 함)")
        print(f"   - 검증 결과: {'✓ 정상' if test_duration == 15 else '✗ 오류'}")
        print()

        # 시험일과 주차 종료일 관계 검증
        days_to_test = (test_start_dt.date() - end_dt.date()).days
        print("4. 시험일과 주차 종료일 관계 검증:")
        print(f"   - 주차 종료일(수요일)부터 시험일(토요일)까지: {days_to_test}일")
        print(f"   - 검증 결과: {'✓ 정상 (3일)' if days_to_test == 3 else '✗ 오류'}")
        print()

        print("=" * 80)
        print("📊 최종 결과 매핑 (로그용):")
        print("=" * 80)
        print()
        print("┌─────────────────────────────────────────────────────────────────────────────┐")
        print("│ INSERT 컬럼 매핑                                                             │")
        print("├─────────────────────────────────────────────────────────────────────────────┤")
        print(f"│ name                  = '{name}'")
        print(f"│ start_date            = '{start_date}'")
        print(f"│ end_date              = '{end_date}'")
        print(f"│ test_start_datetime   = '{test_start_datetime}'")
        print(f"│ test_end_datetime     = '{test_end_datetime}'")
        print("└─────────────────────────────────────────────────────────────────────────────┘")
        print()

        # Python dict 형식으로도 출력
        print("Python Dictionary 형식:")
        print("-" * 80)
        result_dict = {
            "name": name,
            "start_date": start_date,
            "end_date": end_date,
            "test_start_datetime": test_start_datetime,
            "test_end_datetime": test_end_datetime
        }
        import json
        print(json.dumps(result_dict, indent=2, ensure_ascii=False))
        print()

        # JSON Lines 형식 (로그 수집용)
        print("JSON Lines 형식 (로그 수집용):")
        print("-" * 80)
        print(json.dumps(result_dict, ensure_ascii=False))
        print()

        print("=" * 80)
        print("✅ 테스트 완료!")
        print("=" * 80)

    except ValueError as e:
        print(f"❌ 오류: 날짜 형식이 올바르지 않습니다. YYYY-MM-DD 형식으로 입력해주세요.")
        print(f"   상세: {e}")
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()


def main():
    """메인 함수"""
    if len(sys.argv) < 2:
        print("사용법: python test_week_creator_full.py YYYY-MM-DD")
        print()
        print("예시:")
        print("  python test_week_creator_full.py 2025-11-01")
        print("  python test_week_creator_full.py 2025-11-08")
        print("  python test_week_creator_full.py 2025-11-15")
        print()

        # 기본 예시 실행
        print("기본 예시로 오늘 날짜를 사용합니다:")
        print()
        date_string = datetime.now().strftime("%Y-%m-%d")
        test_week_info_values(date_string)
    else:
        date_string = sys.argv[1]
        test_week_info_values(date_string)


if __name__ == "__main__":
    main()

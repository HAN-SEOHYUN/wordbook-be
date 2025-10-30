"""
시험 관리 도구

주차 정보 및 시험 단어 목록을 수동으로 생성할 수 있는 CLI 도구
"""

import argparse
import logging
from datetime import datetime
from core.test_week_creator import TestWeekCreator
from core.test_words_creator import TestWordsCreator

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)


def create_week_info(date_str: str = None):
    """
    test_week_info 생성

    Args:
        date_str: 기준 날짜 (YYYY-MM-DD), None이면 오늘
    """
    logger.info("=" * 80)
    logger.info("시험 주차 정보 생성")
    logger.info("=" * 80)

    base_date = None
    if date_str:
        try:
            base_date = datetime.strptime(date_str, "%Y-%m-%d")
            logger.info(f"기준 날짜: {date_str}")
        except ValueError:
            logger.error(f"잘못된 날짜 형식: {date_str} (YYYY-MM-DD 형식이어야 합니다)")
            return

    creator = TestWeekCreator()
    result = creator.create_week_info(base_date)

    if result:
        logger.info("=" * 80)
        logger.info("✅ 주차 정보 생성 완료!")
        logger.info(f"주차명: {result['name']}")
        logger.info(f"시작일: {result['start_date']}")
        logger.info(f"종료일: {result['end_date']}")
        logger.info(f"토요일: {result['saturday']}")
        logger.info("=" * 80)
    else:
        logger.info("=" * 80)
        logger.info("⚠️ 이미 존재하는 주차입니다.")
        logger.info("=" * 80)


def create_test_words(date_str: str = None, count: int = 30):
    """
    test_words 생성

    Args:
        date_str: 토요일 날짜 (YYYY-MM-DD), None이면 다음 토요일
        count: 선택할 단어 개수
    """
    logger.info("=" * 80)
    logger.info("시험 단어 목록 생성")
    logger.info("=" * 80)

    saturday = None
    if date_str:
        try:
            saturday = datetime.strptime(date_str, "%Y-%m-%d")
            logger.info(f"토요일 날짜: {date_str}")

            # 토요일인지 확인
            if saturday.weekday() != 5:
                logger.warning(f"{date_str}은 토요일이 아닙니다. (요일: {saturday.strftime('%A')})")
                logger.warning("계속 진행합니다...")

        except ValueError:
            logger.error(f"잘못된 날짜 형식: {date_str} (YYYY-MM-DD 형식이어야 합니다)")
            return

    creator = TestWordsCreator()
    result = creator.create_test_words(saturday, count)

    if result:
        logger.info("=" * 80)
        logger.info("✅ 시험 단어 생성 완료!")
        logger.info(f"주차: {result['name']}")
        logger.info(f"시험일: {result['saturday']}")
        logger.info(f"출제범위: {result['start_date']} ~ {result['end_date']}")
        logger.info(f"단어 개수: {result['word_count']}개")
        logger.info("=" * 80)
    else:
        logger.info("=" * 80)
        logger.info("❌ 시험 단어 생성 실패!")
        logger.info("=" * 80)


def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(
        description="시험 관리 도구 - 주차 정보 및 시험 단어 목록 생성"
    )

    parser.add_argument(
        "--create-week-info",
        action="store_true",
        help="test_week_info 생성"
    )

    parser.add_argument(
        "--create-test-words",
        action="store_true",
        help="test_words 생성 (30개 단어 선택)"
    )

    parser.add_argument(
        "--date",
        type=str,
        help="기준 날짜 (YYYY-MM-DD). create-week-info: 해당 주의 정보 생성, create-test-words: 토요일 날짜"
    )

    parser.add_argument(
        "--count",
        type=int,
        default=30,
        help="선택할 단어 개수 (기본: 30)"
    )

    args = parser.parse_args()

    if args.create_week_info:
        create_week_info(args.date)
    elif args.create_test_words:
        create_test_words(args.date, args.count)
    else:
        parser.print_help()
        print("\n사용 예시:")
        print("  python manage_test.py --create-week-info")
        print("  python manage_test.py --create-week-info --date 2025-10-07")
        print("  python manage_test.py --create-test-words")
        print("  python manage_test.py --create-test-words --date 2025-10-11")
        print("  python manage_test.py --create-test-words --date 2025-10-11 --count 20")


if __name__ == "__main__":
    main()

"""
시험 주차 정보 생성기

매주 월요일 00시에 test_week_info 테이블에 이번주 시험 주차 정보를 생성합니다.
"""

from datetime import datetime, timedelta
import logging
from typing import Tuple, Optional
from core.database import DatabaseManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestWeekCreator:
    """시험 주차 정보 생성 클래스"""

    def __init__(self):
        self.db_manager = DatabaseManager()

    def get_this_saturday(self, base_date: Optional[datetime] = None) -> datetime:
        """
        이번주 토요일 날짜 계산

        Args:
            base_date: 기준 날짜 (None이면 오늘)

        Returns:
            이번주 토요일 datetime 객체
        """
        if base_date is None:
            base_date = datetime.now()

        # 0=월요일, 6=일요일
        weekday = base_date.weekday()

        # 토요일(5)까지 며칠 남았는지 계산
        days_until_saturday = (5 - weekday) % 7

        # 오늘이 토요일이면 오늘, 아니면 이번주 토요일
        if days_until_saturday == 0 and weekday == 5:
            saturday = base_date
        else:
            saturday = base_date + timedelta(days=days_until_saturday)

        return saturday.replace(hour=0, minute=0, second=0, microsecond=0)

    def calculate_week_info(self, saturday: datetime) -> Tuple[str, str, str, str, str]:
        """
        토요일 날짜를 기준으로 주차 정보 계산

        Args:
            saturday: 토요일 날짜

        Returns:
            (name, start_date, end_date, test_start_datetime, test_end_datetime) 튜플
            - name: "n월 n주차"
            - start_date: 전주 목요일 (YYYY-MM-DD)
            - end_date: 당주 수요일 (YYYY-MM-DD)
            - test_start_datetime: 토요일 10:10:00 (YYYY-MM-DD HH:MM:SS)
            - test_end_datetime: 토요일 10:25:00 (YYYY-MM-DD HH:MM:SS)
        """
        # 토요일이 속한 월
        month = saturday.month

        # 해당 월의 첫 토요일 찾기
        first_day_of_month = saturday.replace(day=1)

        # 첫 날이 무슨 요일인지 확인 (0=월, 6=일)
        first_weekday = first_day_of_month.weekday()

        # 첫 토요일까지 며칠 남았는지 (5=토요일)
        days_until_first_saturday = (5 - first_weekday) % 7
        first_saturday = first_day_of_month + timedelta(days=days_until_first_saturday)

        # 주차 계산 (첫 토요일부터 몇 주 지났는지)
        week_number = ((saturday - first_saturday).days // 7) + 1

        # name 생성
        name = f"{month}월 {week_number}주차"

        # start_date: 전주 목요일 (토요일 - 9일)
        start_date = (saturday - timedelta(days=9)).strftime("%Y-%m-%d")

        # end_date: 당주 수요일 (토요일 - 3일)
        end_date = (saturday - timedelta(days=3)).strftime("%Y-%m-%d")

        # test_start_datetime: 토요일 10:10:00
        test_start_datetime = saturday.replace(hour=10, minute=10, second=0, microsecond=0).strftime("%Y-%m-%d %H:%M:%S")

        # test_end_datetime: 토요일 10:25:00
        test_end_datetime = saturday.replace(hour=10, minute=25, second=0, microsecond=0).strftime("%Y-%m-%d %H:%M:%S")

        return name, start_date, end_date, test_start_datetime, test_end_datetime

    def create_week_info(self, base_date: Optional[datetime] = None) -> Optional[dict]:
        """
        test_week_info 테이블에 주차 정보 생성

        Args:
            base_date: 기준 날짜 (None이면 오늘)

        Returns:
            생성된 주차 정보 dict 또는 None (이미 존재하는 경우)
        """
        try:
            # 이번주 토요일 계산
            saturday = self.get_this_saturday(base_date)
            saturday_str = saturday.strftime("%Y-%m-%d")

            logger.info(f"이번주 토요일: {saturday_str}")

            # 주차 정보 계산
            name, start_date, end_date, test_start_datetime, test_end_datetime = self.calculate_week_info(saturday)

            logger.info(f"주차 정보: {name}")
            logger.info(f"  - 시작일 (전주 목요일): {start_date}")
            logger.info(f"  - 종료일 (당주 수요일): {end_date}")
            logger.info(f"  - 시험 시작: {test_start_datetime}")
            logger.info(f"  - 시험 종료: {test_end_datetime}")

            # 중복 체크
            with self.db_manager.get_connection() as conn:
                with conn.cursor() as cursor:
                    check_query = """
                    SELECT TWI_ID, NAME FROM test_week_info
                    WHERE NAME = %s
                    """
                    cursor.execute(check_query, (name,))
                    existing = cursor.fetchone()

                    if existing:
                        logger.warning(f"이미 존재하는 주차입니다: {name} (ID: {existing['TWI_ID']})")
                        return None

                    # INSERT
                    insert_query = """
                    INSERT INTO test_week_info (NAME, START_DATE, END_DATE, TEST_START_DATETIME, TEST_END_DATETIME)
                    VALUES (%s, %s, %s, %s, %s)
                    """
                    cursor.execute(insert_query, (name, start_date, end_date, test_start_datetime, test_end_datetime))
                    conn.commit()

                    # 생성된 ID 조회
                    twi_id = cursor.lastrowid

                    logger.info(f"✓ 주차 정보 생성 완료: {name} (ID: {twi_id})")

                    return {
                        "twi_id": twi_id,
                        "name": name,
                        "start_date": start_date,
                        "end_date": end_date,
                        "test_start_datetime": test_start_datetime,
                        "test_end_datetime": test_end_datetime,
                        "saturday": saturday_str
                    }

        except Exception as e:
            logger.error(f"주차 정보 생성 중 오류: {e}", exc_info=True)
            raise


def main():
    """메인 함수 - 수동 실행용"""
    logger.info("=" * 60)
    logger.info("시험 주차 정보 생성")
    logger.info("=" * 60)

    creator = TestWeekCreator()
    result = creator.create_week_info()

    if result:
        logger.info("=" * 60)
        logger.info("✅ 완료!")
        logger.info("=" * 60)
    else:
        logger.info("=" * 60)
        logger.info("⚠️ 이미 존재하는 주차입니다.")
        logger.info("=" * 60)


if __name__ == "__main__":
    main()

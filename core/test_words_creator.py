"""
시험 단어 목록 생성기

매주 금요일 00시에 내일(토요일) 시험 단어 30개를 선택하여 test_words에 저장합니다.
"""

from datetime import datetime, timedelta
import logging
import random
from typing import List, Optional, Dict
from core.database import DatabaseManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestWordsCreator:
    """시험 단어 목록 생성 클래스"""

    def __init__(self):
        self.db_manager = DatabaseManager()

    def get_next_saturday(self, base_date: Optional[datetime] = None) -> datetime:
        """
        다음 토요일 날짜 계산

        Args:
            base_date: 기준 날짜 (None이면 오늘)

        Returns:
            다음 토요일 datetime 객체
        """
        if base_date is None:
            base_date = datetime.now()

        # 0=월요일, 6=일요일
        weekday = base_date.weekday()

        # 금요일(4)이면 다음날(토요일), 아니면 다음 토요일
        if weekday == 4:  # 금요일
            days_until_saturday = 1
        else:
            days_until_saturday = (5 - weekday) % 7
            if days_until_saturday == 0:
                days_until_saturday = 7

        saturday = base_date + timedelta(days=days_until_saturday)
        return saturday.replace(hour=0, minute=0, second=0, microsecond=0)

    def get_test_week_info(self, saturday: datetime) -> Optional[Dict]:
        """
        토요일 날짜로 test_week_info 조회

        Args:
            saturday: 토요일 날짜

        Returns:
            test_week_info dict 또는 None
        """
        saturday_str = saturday.strftime("%Y-%m-%d")

        try:
            with self.db_manager.get_connection() as conn:
                with conn.cursor() as cursor:
                    # 토요일이 포함된 주차 찾기
                    # start_date <= saturday - 3 and end_date >= saturday - 3
                    # 즉, 수요일 날짜로 주차를 찾음
                    wednesday = (saturday - timedelta(days=3)).strftime("%Y-%m-%d")

                    query = """
                    SELECT twi_id, name, start_date, end_date
                    FROM test_week_info
                    WHERE %s BETWEEN start_date AND end_date
                    """
                    cursor.execute(query, (wednesday,))
                    result = cursor.fetchone()

                    if result:
                        return {
                            "twi_id": result["twi_id"],
                            "name": result["name"],
                            "start_date": str(result["start_date"]),
                            "end_date": str(result["end_date"])
                        }
                    else:
                        logger.warning(f"토요일 {saturday_str}에 해당하는 주차 정보가 없습니다.")
                        return None

        except Exception as e:
            logger.error(f"주차 정보 조회 중 오류: {e}", exc_info=True)
            raise

    def get_words_by_date_range(self, start_date: str, end_date: str) -> Dict[str, List[Dict]]:
        """
        날짜 범위의 단어 조회 (날짜별로 그룹화)

        Args:
            start_date: 시작일 (YYYY-MM-DD)
            end_date: 종료일 (YYYY-MM-DD)

        Returns:
            날짜별 단어 목록 dict
            예: {"2025-10-03": [{"wb_id": 1, "word_english": "...", ...}, ...], ...}
        """
        try:
            with self.db_manager.get_connection() as conn:
                with conn.cursor() as cursor:
                    query = """
                    SELECT wb_id, date, word_english, word_meaning
                    FROM word_book
                    WHERE date BETWEEN %s AND %s
                    ORDER BY date, wb_id
                    """
                    cursor.execute(query, (start_date, end_date))
                    results = cursor.fetchall()

                    # 날짜별로 그룹화
                    words_by_date = {}
                    for row in results:
                        wb_id = row["wb_id"]
                        date = row["date"]
                        word_english = row["word_english"]
                        word_meaning = row["word_meaning"]
                        date_str = str(date)

                        if date_str not in words_by_date:
                            words_by_date[date_str] = []

                        words_by_date[date_str].append({
                            "wb_id": wb_id,
                            "date": date_str,
                            "word_english": word_english,
                            "word_meaning": word_meaning
                        })

                    return words_by_date

        except Exception as e:
            logger.error(f"단어 조회 중 오류: {e}", exc_info=True)
            raise

    def select_words_evenly(
        self, words_by_date: Dict[str, List[Dict]], total_count: int = 30, seed: Optional[int] = None
    ) -> List[Dict]:
        """
        날짜별로 최대한 고르게 단어 선택

        Args:
            words_by_date: 날짜별 단어 목록
            total_count: 총 선택할 단어 개수
            seed: 랜덤 시드 (같은 시드면 같은 결과)

        Returns:
            선택된 단어 목록
        """
        if not words_by_date:
            logger.warning("선택할 단어가 없습니다.")
            return []

        # 전체 단어 개수 계산
        total_words = sum(len(words) for words in words_by_date.values())

        if total_words == 0:
            logger.warning("단어가 하나도 없습니다.")
            return []

        if total_words < total_count:
            logger.warning(f"단어가 {total_words}개밖에 없습니다. (목표: {total_count}개)")
            total_count = total_words

        # 랜덤 시드 설정
        if seed is not None:
            random.seed(seed)

        # 날짜별 단어 개수 파악
        logger.info(f"날짜별 단어 개수:")
        for date, words in sorted(words_by_date.items()):
            logger.info(f"  {date}: {len(words)}개")

        # 각 날짜에서 선택할 개수 계산 (비율대로 배분)
        selection_count = {}
        remaining = total_count

        dates = sorted(words_by_date.keys())

        for i, date in enumerate(dates):
            if i == len(dates) - 1:
                # 마지막 날짜는 남은 개수 전부
                selection_count[date] = remaining
            else:
                # 비율대로 계산
                ratio = len(words_by_date[date]) / total_words
                count = int(total_count * ratio)

                # 최소 1개는 선택 (해당 날짜에 단어가 있는 경우)
                if len(words_by_date[date]) > 0 and count == 0:
                    count = 1

                # 남은 개수보다 많으면 조정
                if count > remaining:
                    count = remaining

                selection_count[date] = count
                remaining -= count

        logger.info(f"날짜별 선택 개수:")
        for date in sorted(selection_count.keys()):
            logger.info(f"  {date}: {selection_count[date]}개")

        # 각 날짜에서 랜덤 선택
        selected_words = []

        for date in sorted(dates):
            count = selection_count[date]
            available_words = words_by_date[date]

            if count > len(available_words):
                count = len(available_words)

            if count > 0:
                chosen = random.sample(available_words, count)
                selected_words.extend(chosen)

        logger.info(f"총 {len(selected_words)}개 단어 선택 완료")

        return selected_words

    def create_test_words(self, saturday: Optional[datetime] = None, word_count: int = 30) -> Optional[Dict]:
        """
        test_words 테이블에 시험 단어 목록 생성

        Args:
            saturday: 토요일 날짜 (None이면 다음 토요일)
            word_count: 선택할 단어 개수 (기본 30개)

        Returns:
            생성 결과 dict 또는 None
        """
        try:
            # 토요일 날짜 계산
            if saturday is None:
                saturday = self.get_next_saturday()

            saturday_str = saturday.strftime("%Y-%m-%d")
            logger.info(f"시험 날짜 (토요일): {saturday_str}")

            # test_week_info 조회
            week_info = self.get_test_week_info(saturday)

            if not week_info:
                logger.error(f"토요일 {saturday_str}에 해당하는 주차 정보를 찾을 수 없습니다.")
                logger.error("먼저 test_week_info를 생성해야 합니다.")
                return None

            twi_id = week_info["twi_id"]
            name = week_info["name"]
            start_date = week_info["start_date"]
            end_date = week_info["end_date"]

            logger.info(f"주차: {name} (ID: {twi_id})")
            logger.info(f"출제 범위: {start_date} ~ {end_date}")

            # 해당 범위의 단어 조회
            words_by_date = self.get_words_by_date_range(start_date, end_date)

            if not words_by_date:
                logger.error(f"출제 범위({start_date} ~ {end_date})에 단어가 없습니다.")
                return None

            # 고정 시드로 랜덤 선택 (모든 사용자가 같은 결과)
            seed = int(saturday.timestamp())
            selected_words = self.select_words_evenly(words_by_date, word_count, seed)

            if not selected_words:
                logger.error("선택된 단어가 없습니다.")
                return None

            # 기존 데이터 삭제 (재생성 허용)
            with self.db_manager.get_connection() as conn:
                with conn.cursor() as cursor:
                    delete_query = """
                    DELETE FROM test_words WHERE twi_id = %s
                    """
                    cursor.execute(delete_query, (twi_id,))
                    deleted_count = cursor.rowcount

                    if deleted_count > 0:
                        logger.info(f"기존 데이터 {deleted_count}개 삭제")

                    # test_words에 INSERT
                    insert_query = """
                    INSERT INTO test_words (twi_id, wb_id)
                    VALUES (%s, %s)
                    """

                    for word in selected_words:
                        cursor.execute(insert_query, (twi_id, word["wb_id"]))

                    conn.commit()

                    logger.info(f"✓ {len(selected_words)}개 단어 저장 완료")

                    return {
                        "twi_id": twi_id,
                        "name": name,
                        "saturday": saturday_str,
                        "start_date": start_date,
                        "end_date": end_date,
                        "word_count": len(selected_words),
                        "words": selected_words
                    }

        except Exception as e:
            logger.error(f"시험 단어 생성 중 오류: {e}", exc_info=True)
            raise


def main():
    """메인 함수 - 수동 실행용"""
    logger.info("=" * 60)
    logger.info("시험 단어 목록 생성")
    logger.info("=" * 60)

    creator = TestWordsCreator()
    result = creator.create_test_words()

    if result:
        logger.info("=" * 60)
        logger.info("✅ 완료!")
        logger.info(f"주차: {result['name']}")
        logger.info(f"단어 개수: {result['word_count']}개")
        logger.info("=" * 60)
    else:
        logger.info("=" * 60)
        logger.info("❌ 실패!")
        logger.info("=" * 60)


if __name__ == "__main__":
    main()

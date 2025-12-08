from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import logging
import requests

# config import
import config

# 로깅 설정 (config에서 읽기)
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format=config.LOG_FORMAT,
    datefmt=config.LOG_DATE_FORMAT,
)
logger = logging.getLogger(__name__)


class BBCLearningEnglishCrawler:
    """BBC Learning English 6 Minute English 영단어 크롤러"""

    BASE_URL = "https://www.bbc.co.uk/learningenglish/english/features/6-minute-english"

    def __init__(self):
        """크롤러 초기화"""
        logger.info("BBC Learning English 크롤러 초기화")

    def calculate_last_thursday(self):
        """
        날짜 계산 함수
        
        우선순위:
        1. config.BBC_DAYS_AGO가 설정되어 있으면 해당 일수 전 날짜 사용
        2. config.BBC_TARGET_DATE가 설정되어 있으면 해당 특정 날짜 사용
        3. 둘 다 None이면 자동으로 전주 목요일 계산 (기존 로직)

        Returns:
            tuple: (URL용 날짜(YYMMDD), DB용 날짜(YYYY-MM-DD))
        """
        # 우선순위 1: config.BBC_DAYS_AGO
        if config.BBC_DAYS_AGO is not None:
            target_date = datetime.now() - timedelta(days=config.BBC_DAYS_AGO)
            logger.info(f"날짜 계산 방식: 상대 날짜 ({config.BBC_DAYS_AGO}일 전)")
        # 우선순위 2: config.BBC_TARGET_DATE
        elif config.BBC_TARGET_DATE is not None:
            target_date = datetime.strptime(config.BBC_TARGET_DATE, "%Y-%m-%d")
            logger.info(f"날짜 계산 방식: 특정 날짜 ({config.BBC_TARGET_DATE})")
        # 우선순위 3: 자동 계산 (전주 목요일)
        else:
            today = datetime.now()

            # 오늘이 무슨 요일인지 확인 (0=월요일, 6=일요일)
            days_since_thursday = (today.weekday() - 3) % 7

            # 전주 목요일까지의 일수 계산
            # 오늘이 목요일이면 7일 전, 금요일이면 8일 전, 수요일이면 6일 전
            if days_since_thursday == 0:
                # 오늘이 목요일인 경우 지난주 목요일
                days_to_subtract = 7
            else:
                # 다른 요일인 경우 이번주 또는 지난주 목요일
                days_to_subtract = days_since_thursday + 7 if days_since_thursday < 4 else days_since_thursday

            target_date = today - timedelta(days=days_to_subtract)
            logger.info(f"날짜 계산 방식: 자동 계산 (전주 목요일)")

        # URL용 형식: YYMMDD (예: 251023)
        url_format = target_date.strftime("%y%m%d")

        # DB용 형식: YYYY-MM-DD (예: 2025-10-23)
        db_format = target_date.strftime("%Y-%m-%d")

        # 표시용 형식: YYYY.MM.DD
        display_format = target_date.strftime("%Y.%m.%d")

        logger.info(f"대상 날짜: {display_format}")

        return url_format, db_format

    def construct_url(self, date_str):
        """
        BBC 6 Minute English URL 생성

        Args:
            date_str: YYMMDD 형식의 날짜 문자열

        Returns:
            str: 완성된 URL
        """
        # 현재 연도를 4자리로 가져오기
        current_year = datetime.now().year

        # URL 구성: https://www.bbc.co.uk/learningenglish/english/features/6-minute-english_2025/ep-251023
        url = f"{self.BASE_URL}_{current_year}/ep-{date_str}"

        logger.info(f"생성된 URL: {url}")
        return url

    def extract_vocabulary(self, url):
        """
        BBC 페이지에서 영단어 추출

        Args:
            url: BBC 6 Minute English 페이지 URL

        Returns:
            list: 영단어 딕셔너리 리스트 [{"english_word": ..., "korean_meaning": ...}, ...]
        """
        try:
            logger.info("BBC 페이지 접속 중...")

            response = requests.get(url, timeout=config.HTTP_TIMEOUT)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "lxml")

            # <h3>Vocabulary</h3> 찾기
            vocabulary_header = soup.find("h3", string="Vocabulary")

            if not vocabulary_header:
                logger.error("Vocabulary 섹션을 찾을 수 없습니다.")
                return []

            logger.info("Vocabulary 섹션 발견")

            # Vocabulary 헤더 다음의 <p> 태그 찾기
            vocabulary_paragraph = vocabulary_header.find_next_sibling("p")

            if not vocabulary_paragraph:
                logger.error("Vocabulary 데이터를 포함한 <p> 태그를 찾을 수 없습니다.")
                return []

            # <p> 내부의 모든 내용 파싱
            words = []
            current_word = None
            current_meaning = []

            for element in vocabulary_paragraph.children:
                if element.name == "strong":
                    # 이전 단어가 있으면 저장
                    if current_word:
                        meaning_text = " ".join(current_meaning).strip()
                        if meaning_text:
                            words.append({
                                "english_word": current_word,
                                "korean_meaning": meaning_text
                            })

                    # 새로운 단어 시작
                    current_word = element.get_text().strip()
                    current_meaning = []

                elif element.name == "br":
                    # <br> 태그는 건너뜀
                    continue

                elif isinstance(element, str):
                    # 텍스트 노드
                    text = element.strip()
                    if text and current_word:
                        current_meaning.append(text)

            # 마지막 단어 저장
            if current_word:
                meaning_text = " ".join(current_meaning).strip()
                if meaning_text:
                    words.append({
                        "english_word": current_word,
                        "korean_meaning": meaning_text
                    })

            logger.info(f"✓ 총 {len(words)}개의 단어 추출 완료")

            for idx, word in enumerate(words, 1):
                logger.info(f"  [{idx}] {word['english_word']} : {word['korean_meaning']}")

            return words

        except requests.exceptions.RequestException as e:
            logger.error(f"HTTP 요청 중 에러 발생: {e}")
            return []
        except Exception as e:
            logger.error(f"영단어 추출 중 에러 발생: {e}")
            import traceback
            traceback.print_exc()
            return []

    def save_to_database(self, date, words, source_url):
        """DB 저장 (config.DIRECT_DB_SAVE에 따라 API 또는 직접 저장)"""

        if config.DIRECT_DB_SAVE:
            self._save_to_db_directly(date, words, source_url)
        else:
            self._save_via_api(date, words, source_url)

    def _save_via_api(self, date, words, source_url):
        """API를 통해 저장"""

        success_count = 0
        fail_count = 0

        logger.info(f"API를 통해 저장 중...")

        for word in words:
            try:
                data = {
                    "date": date,
                    "english_word": word["english_word"],
                    "korean_meaning": word["korean_meaning"],
                    "source_url": source_url,
                }

                response = requests.post(
                    config.API_ENDPOINT, json=data, timeout=config.HTTP_TIMEOUT
                )

                if response.status_code in [200, 201]:
                    success_count += 1
                else:
                    fail_count += 1
                    logger.warning(f"  ✗ 저장 실패: {word['english_word']}")

            except Exception as e:
                fail_count += 1
                logger.error(f"  ✗ 저장 중 에러: {word['english_word']} - {e}")

        logger.info(f"저장 완료: 성공 {success_count}개, 실패 {fail_count}개")

    def _save_to_db_directly(self, date, words, source_url):
        """DB에 직접 저장"""
        from core.database import DatabaseManager

        logger.info(f"DB에 직접 저장 중...")

        db_manager = DatabaseManager()

        upsert_query = """
        INSERT INTO word_book (DATE, WORD_ENGLISH, WORD_MEANING, SOURCE_URL)
        VALUES (%s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            WORD_MEANING = VALUES(WORD_MEANING),
            SOURCE_URL = VALUES(SOURCE_URL),
            UPDATED_AT = CURRENT_TIMESTAMP;
        """

        success_count = 0
        fail_count = 0

        try:
            with db_manager.get_connection() as conn:
                with conn.cursor() as cursor:
                    for word in words:
                        try:
                            cursor.execute(
                                upsert_query,
                                (date, word["english_word"], word["korean_meaning"], source_url),
                            )
                            success_count += 1
                        except Exception as e:
                            fail_count += 1
                            logger.error(f"  ✗ 저장 실패: {word['english_word']} - {e}")

                    conn.commit()

            logger.info(f"저장 완료: 성공 {success_count}개, 실패 {fail_count}개")

        except Exception as e:
            logger.error(f"DB 저장 중 에러: {e}")

    def run(self):
        """크롤러 실행"""
        try:
            logger.info("=" * 60)
            logger.info("BBC Learning English 6 Minute English 크롤러 시작")
            logger.info("=" * 60)

            # 설정 출력
            config.print_config()

            # 전주 목요일 날짜 계산
            url_date, db_date = self.calculate_last_thursday()

            # URL 생성
            url = self.construct_url(url_date)

            # 영단어 추출
            words = self.extract_vocabulary(url)

            if not words:
                logger.warning("추출된 단어가 없습니다.")
                return

            # DB 저장
            logger.info(f"데이터베이스 저장 시작 (날짜: {db_date})")
            self.save_to_database(db_date, words, url)

            logger.info("=" * 60)
            logger.info("✅ 크롤러 실행 완료!")
            logger.info("=" * 60)

        except Exception as e:
            logger.error(f"크롤러 실행 중 에러: {e}", exc_info=True)

    def close(self):
        """리소스 정리 (필요시 구현)"""
        logger.info("크롤러 종료")


def main():
    """메인 함수"""
    # 설정 검증
    try:
        config.validate_config()
    except ValueError as e:
        logger.error(f"설정 오류: {e}")
        return

    crawler = BBCLearningEnglishCrawler()
    crawler.run()
    crawler.close()


if __name__ == "__main__":
    main()

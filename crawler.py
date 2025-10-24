from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import re
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


class EBSMorningCrawler:
    """EBS 모닝스페셜 영단어 크롤러"""

    # 정규표현식 패턴
    WORD_PATTERN = re.compile(r"▶\s*(.*?)\s*:\s*(.*?)(?=\s*▶|\Z)", re.DOTALL)
    NON_BULLET_WORD_PATTERN = re.compile(
        r"([a-zA-Z\s\-\/]+?):\s*(.*?)(?=\s*▶|\s*[a-zA-Z\s\-\/]+?:|\Z)", re.DOTALL
    )

    def __init__(self):
        """크롤러 초기화 (config에서 설정 읽기)"""
        chrome_options = Options()

        if config.HEADLESS_MODE:
            chrome_options.add_argument("--headless")

        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )

        # ChromeDriver 설치 및 경로 가져오기
        driver_path = ChromeDriverManager().install()
        logger.info(f"ChromeDriver path: {driver_path}")

        # 경로가 THIRD_PARTY_NOTICES 파일을 가리키는 경우 수정
        if "THIRD_PARTY_NOTICES" in driver_path:
            import os
            driver_dir = os.path.dirname(driver_path)
            driver_path = os.path.join(driver_dir, "chromedriver.exe")
            logger.info(f"Fixed ChromeDriver path: {driver_path}")

        service = Service(driver_path)
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.wait = WebDriverWait(self.driver, config.PAGE_LOAD_TIMEOUT)

    def calculate_target_date(self, days_ago: int):
        """
        날짜 계산 함수

        Args:
            days_ago: 며칠 전

        Returns:
            tuple: (표시용 날짜, DB용 날짜)
        """
        target_date = datetime.now() - timedelta(days=days_ago)
        display_format = target_date.strftime("%Y.%m.%d")
        db_format = target_date.strftime("%Y-%m-%d")
        return display_format, db_format

    def find_article_by_date(self, target_date: str):
        """게시판에서 특정 날짜의 게시글 찾기"""
        try:
            logger.info(f"게시판 페이지 접속 중...")
            self.driver.get(config.BOARD_URL)

            self.wait.until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "#itemList > tr"))
            )
            logger.info("페이지 로드 완료")

            rows = self.driver.find_elements(
                By.CSS_SELECTOR, "#itemList > tr:not(.notice)"
            )
            logger.info(f"총 {len(rows)}개의 일반 게시글 발견")

            for idx, row in enumerate(rows, 1):
                try:
                    tds = row.find_elements(By.TAG_NAME, "td")

                    if len(tds) < 5:
                        continue

                    # 게시글 제목을 가져옵니다. (방송일 정보가 포함되어 있을 가능성이 높음)
                    link_element = tds[1].find_element(By.TAG_NAME, "a")
                    title = link_element.text.strip()

                    # 게시판 목록의 날짜도 가져옵니다. (디버깅/정보용)
                    date_text = tds[3].text.strip()

                    # ⭐ 핵심 수정: 게시판 날짜 대신, 게시글 제목에 'target_date'가 포함되어 있는지 확인합니다.
                    # target_date는 'YYYY.MM.DD' 형식이고, title은 'YYYY.MM.DD. Day. (...)' 형식일 수 있습니다.
                    if target_date in title:

                        href = link_element.get_attribute("href")

                        if href.startswith("/"):
                            full_url = config.BASE_URL + href
                        else:
                            full_url = href

                        logger.info(f"✓ 발견: {title} (게시일: {date_text})")
                        logger.info(f"  URL: {full_url}")

                        return full_url

                except Exception as e:
                    logger.debug(f"게시글 {idx} 처리 중 에러: {e}")
                    continue

            logger.warning(f"{target_date} 날짜의 게시글을 찾을 수 없습니다.")
            return None

        except Exception as e:
            logger.error(f"게시판 조회 중 에러 발생: {e}")
            return None

    def clean_korean_translation(
        self, raw_kor: str, log_prefix: str, final_matches: list
    ) -> str:
        """한글 해석 클리닝"""
        clean_kor = raw_kor

        relieve_pattern = r"relieve oneself\[nature\]\s*:\s*대소변을 보다"
        relieve_match = re.search(relieve_pattern, clean_kor, re.DOTALL | re.IGNORECASE)

        if relieve_match:
            relieve_entry_text = relieve_match.group(0).strip()
            relieve_parts = relieve_entry_text.split(":")

            if len(relieve_parts) == 2:
                relieve_eng = relieve_parts[0].strip().replace("[nature]", "").strip()
                relieve_kor = relieve_parts[1].strip()
                final_matches.append((relieve_eng, relieve_kor))
                logger.debug(f"{log_prefix} [Clean] Extracted 'relieve oneself'.")

            cut_index = relieve_match.start()
            clean_kor = clean_kor[:cut_index].strip()

        news_body_start_match = re.search(
            r"\s*\d+\.\s*([A-Z]|\s*서울시는|\s*영국|\s*미국의)", clean_kor, re.DOTALL
        )

        if news_body_start_match:
            cut_index = news_body_start_match.start()
            clean_kor = clean_kor[:cut_index].strip()
            logger.debug(f"{log_prefix} [Clean] Cut at News Item Start")

        expression_marker = "Expression"
        if expression_marker in clean_kor:
            cut_index = clean_kor.find(expression_marker)
            clean_kor = clean_kor[:cut_index].strip()
            logger.debug(f"{log_prefix} [Clean] Cut at Expression Marker")

        return clean_kor.strip()

    def extract_vocabulary(self, article_url):
        """게시글에서 영단어 추출"""
        try:
            logger.info("게시글 상세 페이지 접속 중...")

            response = requests.get(article_url, timeout=config.HTTP_TIMEOUT)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "lxml")
            body_container = soup.select_one(config.BODY_SELECTOR)

            if not body_container:
                logger.error(
                    f"Selector '{config.BODY_SELECTOR}'를 사용하여 본문을 찾을 수 없습니다."
                )
                return []

            raw_text = " ".join(body_container.stripped_strings)
            full_text = re.sub(r"\s+", " ", raw_text).strip()

            logger.info(f"본문 텍스트 추출 완료 (길이: {len(full_text)}자)")

            parts = full_text.split("Expression ]")
            vocabulary_text = " ".join([part.strip() for part in parts[1:]])

            vocabulary_text = vocabulary_text.split("idiom package")[0].strip()
            vocabulary_text = re.split(r"-{10,}", vocabulary_text)[0].strip()
            vocabulary_text = vocabulary_text.split(
                "NEWS COVERAGE FROM THE NEW YORK TIMES"
            )[0].strip()

            final_matches = []

            matches_bullet = self.WORD_PATTERN.findall(vocabulary_text)

            for i, (eng, raw_kor) in enumerate(matches_bullet):
                log_prefix = f"[단어 {i+1:02d}] '{eng.strip()[:20]}...'"
                clean_kor = self.clean_korean_translation(
                    raw_kor, log_prefix, final_matches
                )
                final_matches.append((eng.strip(), clean_kor))

            matches_non_bullet = self.NON_BULLET_WORD_PATTERN.findall(vocabulary_text)
            bullet_engs = {m[0] for m in final_matches}

            for eng, raw_kor in matches_non_bullet:
                if eng.strip() not in bullet_engs and len(eng.strip()) > 2:
                    clean_kor = raw_kor.strip().split("Expression")[0].strip()
                    clean_kor = re.split(r"\d+\.\s*", clean_kor)[0].strip()

                    if not clean_kor.startswith(eng):
                        final_matches.append((eng.strip(), clean_kor))

            logger.info(f"✓ 총 {len(final_matches)}개의 단어 추출 완료")

            for idx, (eng, kor) in enumerate(final_matches, 1):
                logger.info(f"  [{idx}] {eng} : {kor}")

            words = [
                {"english_word": eng, "korean_meaning": kor}
                for eng, kor in final_matches
            ]

            return words

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
        INSERT INTO daily_vocabulary (date, english_word, korean_meaning, source_url)
        VALUES (%s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            korean_meaning = VALUES(korean_meaning),
            source_url = VALUES(source_url),
            updated_at = CURRENT_TIMESTAMP;
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
            logger.info("EBS 모닝스페셜 영단어 크롤러 시작")
            logger.info("=" * 60)

            # 설정 출력
            config.print_config()

            # 날짜 계산
            display_date, db_date = self.calculate_target_date(config.DAYS_AGO)
            logger.info(f"대상 날짜: {display_date} (DB: {db_date})")

            # 재시도 로직
            if config.AUTO_RETRY_PREVIOUS_DATE:
                logger.info(
                    f"자동 재시도 활성화: 최대 {config.MAX_RETRY_DAYS}일 전까지 시도"
                )
                date_range = []
                for i in range(
                    config.DAYS_AGO, config.DAYS_AGO + config.MAX_RETRY_DAYS
                ):
                    date_range.append(self.calculate_target_date(i))
            else:
                date_range = [(display_date, db_date)]

            article_url = None
            selected_db_date = None

            # 날짜별 게시글 검색
            for display, db in date_range:
                logger.info(f"📅 날짜 시도: {display}")
                article_url = self.find_article_by_date(display)

                if article_url:
                    selected_db_date = db
                    break

            if not article_url:
                logger.warning("크롤링할 게시글이 없습니다.")
                return

            # 영단어 추출
            words = self.extract_vocabulary(article_url)

            if not words:
                logger.warning("추출된 단어가 없습니다.")
                return

            # DB 저장
            logger.info(f"데이터베이스 저장 시작 (날짜: {selected_db_date})")
            self.save_to_database(selected_db_date, words, article_url)

            logger.info("=" * 60)
            logger.info("✅ 크롤러 실행 완료!")
            logger.info("=" * 60)

        except Exception as e:
            logger.error(f"크롤러 실행 중 에러: {e}", exc_info=True)
        finally:
            self.close()

    def close(self):
        """브라우저 종료"""
        if self.driver:
            self.driver.quit()
            logger.info("브라우저 종료")


def main():
    """메인 함수"""
    # 설정 검증
    try:
        config.validate_config()
    except ValueError as e:
        logger.error(f"설정 오류: {e}")
        return

    crawler = EBSMorningCrawler()
    crawler.run()


if __name__ == "__main__":
    main()

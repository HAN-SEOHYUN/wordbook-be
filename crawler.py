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
import time
import logging
import requests

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


class EBSMorningCrawler:
    """EBS 모닝스페셜 영단어 크롤러"""

    BASE_URL = "https://home.ebs.co.kr"
    BOARD_URL = "https://home.ebs.co.kr/morning/board/6/502387/list?hmpMnuId=101"
    BODY_SELECTOR = "div.con_txt"

    # 정규표현식 패턴
    WORD_PATTERN = re.compile(r"▶\s*(.*?)\s*:\s*(.*?)(?=\s*▶|\Z)", re.DOTALL)
    NON_BULLET_WORD_PATTERN = re.compile(
        r"([a-zA-Z\s\-\/]+?):\s*(.*?)(?=\s*▶|\s*[a-zA-Z\s\-\/]+?:|\Z)", re.DOTALL
    )

    def __init__(self, headless=True):
        chrome_options = Options()
        if headless:
            chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )

        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.wait = WebDriverWait(self.driver, 10)

    def get_yesterday_date(self):
        """어제 날짜 계산"""
        yesterday = datetime.now() - timedelta(days=1)
        display_format = yesterday.strftime("%Y.%m.%d")
        db_format = yesterday.strftime("%Y-%m-%d")
        return display_format, db_format

    def find_article_by_date(self, target_date):
        """게시판에서 특정 날짜의 게시글 찾기"""
        try:
            logger.info(f"게시판 페이지 접속 중...")
            self.driver.get(self.BOARD_URL)

            # 게시글 목록이 로드될 때까지 대기
            self.wait.until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "#itemList > tr"))
            )
            logger.info("페이지 로드 완료")

            # 게시글 목록 가져오기 (공지사항 제외)
            rows = self.driver.find_elements(
                By.CSS_SELECTOR, "#itemList > tr:not(.notice)"
            )
            logger.info(f"총 {len(rows)}개의 일반 게시글 발견")

            for idx, row in enumerate(rows, 1):
                try:
                    tds = row.find_elements(By.TAG_NAME, "td")

                    if len(tds) < 5:
                        continue

                    # 날짜는 4번째 td (인덱스 3)
                    date_text = tds[3].text.strip()

                    if date_text == target_date:
                        # 제목 컬럼에서 링크 추출
                        link_element = tds[1].find_element(By.TAG_NAME, "a")
                        href = link_element.get_attribute("href")

                        if href.startswith("/"):
                            full_url = self.BASE_URL + href
                        else:
                            full_url = href

                        title = link_element.text.strip()
                        logger.info(f"✓ 발견: {title}")
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
        """
        한글 해석 문자열에서 불필요하게 섞여 들어간 기사 본문 및 다른 어휘 항목을 제거
        """
        clean_kor = raw_kor

        # 1. 'relieve oneself' 항목 처리
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

        # 2. 다음 뉴스 기사 번호 시작 패턴
        news_body_start_match = re.search(
            r"\s*\d+\.\s*([A-Z]|\s*서울시는|\s*영국|\s*미국의)", clean_kor, re.DOTALL
        )

        if news_body_start_match:
            cut_index = news_body_start_match.start()
            clean_kor = clean_kor[:cut_index].strip()
            logger.debug(f"{log_prefix} [Clean] Cut at News Item Start")

        # 3. 'Expression' 마커
        expression_marker = "Expression"
        if expression_marker in clean_kor:
            cut_index = clean_kor.find(expression_marker)
            clean_kor = clean_kor[:cut_index].strip()
            logger.debug(f"{log_prefix} [Clean] Cut at Expression Marker")

        return clean_kor.strip()

    def extract_vocabulary(self, article_url):
        """게시글에서 영단어 추출 (BeautifulSoup + 정규표현식)"""
        try:
            logger.info("게시글 상세 페이지 접속 중...")

            # requests로 HTML 가져오기 (더 빠름)
            response = requests.get(article_url, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "lxml")
            body_container = soup.select_one(self.BODY_SELECTOR)

            if not body_container:
                logger.error(
                    f"Selector '{self.BODY_SELECTOR}'를 사용하여 본문을 찾을 수 없습니다."
                )
                return []

            # 본문 텍스트 추출
            raw_text = " ".join(body_container.stripped_strings)
            full_text = re.sub(r"\s+", " ", raw_text).strip()

            logger.info(f"본문 텍스트 추출 완료 (길이: {len(full_text)}자)")

            # 'Expression ]' 섹션 이후만 사용
            parts = full_text.split("Expression ]")
            vocabulary_text = " ".join([part.strip() for part in parts[1:]])

            # 후반부 불필요한 섹션 제거
            vocabulary_text = vocabulary_text.split("idiom package")[0].strip()
            vocabulary_text = re.split(r"-{10,}", vocabulary_text)[0].strip()
            vocabulary_text = vocabulary_text.split(
                "NEWS COVERAGE FROM THE NEW YORK TIMES"
            )[0].strip()

            final_matches = []

            # --- 표준 패턴 추출 (▶ 기호로 시작하는 단어들) ---
            matches_bullet = self.WORD_PATTERN.findall(vocabulary_text)

            for i, (eng, raw_kor) in enumerate(matches_bullet):
                log_prefix = f"[단어 {i+1:02d}] '{eng.strip()[:20]}...'"

                # 한글 해석 클리닝
                clean_kor = self.clean_korean_translation(
                    raw_kor, log_prefix, final_matches
                )

                # 최종 단어 추가
                final_matches.append((eng.strip(), clean_kor))

            # --- 비표준 패턴 추출 (NYT 섹션의 단어들) ---
            matches_non_bullet = self.NON_BULLET_WORD_PATTERN.findall(vocabulary_text)

            bullet_engs = {m[0] for m in final_matches}

            for eng, raw_kor in matches_non_bullet:
                if eng.strip() not in bullet_engs and len(eng.strip()) > 2:
                    clean_kor = raw_kor.strip().split("Expression")[0].strip()
                    clean_kor = re.split(r"\d+\.\s*", clean_kor)[0].strip()

                    if not clean_kor.startswith(eng):
                        final_matches.append((eng.strip(), clean_kor))

            logger.info(f"✓ 총 {len(final_matches)}개의 단어 추출 완료")

            # 추출된 단어 샘플 출력 (처음 5개)
            for idx, (eng, kor) in enumerate(final_matches[:5], 1):
                logger.info(f"  [{idx}] {eng} : {kor}")

            if len(final_matches) > 5:
                logger.info(f"  ... 외 {len(final_matches) - 5}개")

            # 튜플 리스트를 딕셔너리 리스트로 변환
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

    def save_to_database(self, date, words):
        """DB 저장"""
        import requests

        api_url = "http://localhost:8000/api/v1/vocabulary/"

        success_count = 0
        fail_count = 0

        logger.info(f"데이터베이스 저장 시작...")

        for word in words:
            try:
                data = {
                    "date": date,
                    "english_word": word["english_word"],
                    "korean_meaning": word["korean_meaning"],
                }

                response = requests.post(api_url, json=data, timeout=10)

                if response.status_code in [200, 201]:
                    success_count += 1
                else:
                    fail_count += 1
                    logger.warning(f"  ✗ 저장 실패: {word['english_word']}")

            except Exception as e:
                fail_count += 1
                logger.error(f"  ✗ 저장 중 에러: {word['english_word']} - {e}")

        logger.info(f"저장 완료: 성공 {success_count}개, 실패 {fail_count}개")

    def run(self):
        """크롤러 실행"""
        try:
            logger.info("=" * 60)
            logger.info("EBS 모닝스페셜 영단어 크롤러 시작")
            logger.info("=" * 60)

            # 1. 어제 날짜 계산
            display_date, db_date = self.get_yesterday_date()
            logger.info(f"대상 날짜: {display_date} (DB: {db_date})")

            # 2. 게시판에서 어제 날짜 게시글 찾기
            article_url = self.find_article_by_date(display_date)

            if not article_url:
                logger.warning("크롤링할 게시글이 없습니다.")
                return

            # 3. 영단어 추출
            words = self.extract_vocabulary(article_url)

            if not words:
                logger.warning("추출된 단어가 없습니다.")
                return

            # 4. DB 저장
            logger.info(f"데이터베이스 저장 시작 (날짜: {db_date})")
            self.save_to_database(db_date, words)

            logger.info("=" * 60)
            logger.info("크롤러 실행 완료!")
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
    crawler = EBSMorningCrawler(headless=True)  # headless=True로 백그라운드 실행
    crawler.run()


if __name__ == "__main__":
    main()

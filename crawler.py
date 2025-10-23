import requests
import re
from bs4 import BeautifulSoup
import pymysql
import pymysql.cursors
from contextlib import contextmanager
from datetime import datetime
import logging
import os
from dotenv import load_dotenv  # 환경 변수 로드를 위해 필요
from typing import List, Tuple

# 로깅 설정
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


# --- DB 연결 및 관리 클래스 (사용자 제공) ---
class DatabaseManager:
    """환경 변수를 통해 MySQL 연결 정보를 관리하고 커넥션을 제공하는 클래스입니다."""

    def __init__(self):
        # 환경 변수 로드 (스크립트 실행 시 .env 파일이 존재하는 경우)
        load_dotenv(".env.dev")

        try:
            # 1. DB_HOST (필수)
            self.host = os.environ["DB_HOST"]
            # 3. DB_USER (필수)
            self.user = os.environ["DB_USER"]
            # 4. DB_PASSWORD (필수)
            self.password = os.environ["DB_PASSWORD"]
            # 5. DB_DATABASE (필수)
            self.database = os.environ["DB_DATABASE"]
        except KeyError as e:
            logging.error(
                f"필수 환경 변수 {e}가 설정되지 않았습니다. .env.dev 파일을 확인하세요."
            )
            raise

        # 2. DB_PORT (기본값: 3306)
        try:
            port_str = os.getenv("DB_PORT", "3306")
            self.port = int(port_str)
        except ValueError:
            logging.error(
                f"DB_PORT 환경 변수({port_str})가 유효한 숫자가 아닙니다. 3306을 사용합니다."
            )
            self.port = 3306

        logging.info("DatabaseManager 초기화 완료.")

    @contextmanager
    def get_connection(self):
        """MySQL 연결을 생성하고 관리하는 컨텍스트 매니저입니다."""
        connection = None
        try:
            connection = pymysql.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                database=self.database,
                charset="utf8mb4",
                cursorclass=pymysql.cursors.DictCursor,
                autocommit=False,
                init_command="SET time_zone='+09:00'",
            )
            yield connection
        except Exception as e:
            if connection:
                connection.rollback()
            logging.error(f"Database error: {e}")
            # 에러를 재발생시켜 호출자에게 알립니다.
            raise
        finally:
            if connection:
                connection.close()


# --- 크롤링 및 정규 표현식 설정 ---
ARTICLE_URL = "https://home.ebs.co.kr/morning/board/6/502387/view/30000321510?c.page=1"
BODY_SELECTOR = "div.con_txt"

WORD_PATTERN = re.compile(r"▶\s*(.*?)\s*:\s*(.*?)(?=\s*▶|\Z)", re.DOTALL)
NON_BULLET_WORD_PATTERN = re.compile(
    r"([a-zA-Z\s\-\/]+?):\s*(.*?)(?=\s*▶|\s*[a-zA-Z\s\-\/]+?:|\Z)", re.DOTALL
)


# --- 크롤링 핵심 로직 함수 (이전 단계 검증 완료된 코드) ---


def clean_korean_translation(raw_kor: str, log_prefix: str, final_matches: list) -> str:
    """
    한글 해석 문자열에서 불필요하게 섞여 들어간 기사 본문 및 다른 어휘 항목을 제거하고,
    분리되어야 하는 어휘 항목(relieve oneself)을 별도로 추출합니다.
    """
    clean_kor = raw_kor

    # 1. 분리되어야 하는 어휘 항목('relieve oneself') 처리
    relieve_pattern = r"relieve oneself\[nature\]\s*:\s*대소변을 보다"
    relieve_match = re.search(relieve_pattern, clean_kor, re.DOTALL | re.IGNORECASE)

    if relieve_match:
        relieve_entry_text = relieve_match.group(0).strip()
        relieve_parts = relieve_entry_text.split(":")

        if len(relieve_parts) == 2:
            relieve_eng = relieve_parts[0].strip().replace("[nature]", "").strip()
            relieve_kor = relieve_parts[1].strip()
            final_matches.append((relieve_eng, relieve_kor))
            logging.debug(f"{log_prefix} [Clean] Extracted and Cut 'relieve oneself'.")

        # 기존 단어의 한글 해석은 'relieve oneself' 앞에서 자른다.
        cut_index = relieve_match.start()
        clean_kor = clean_kor[:cut_index].strip()

    # 2. 다음 뉴스 기사 번호 시작 패턴 (예: "2. Seoul...")을 찾고 그 앞에서 자른다.
    news_body_start_match = re.search(
        r"\s*\d+\.\s*([A-Z]|\s*서울시는|\s*영국|\s*미국의)", clean_kor, re.DOTALL
    )

    if news_body_start_match:
        cut_index = news_body_start_match.start()
        clean_kor = clean_kor[:cut_index].strip()
        logging.debug(
            f"{log_prefix} [Clean] Cut at News Item Start (Index {cut_index})"
        )

    # 3. 'Expression' 마커를 찾고 그 앞에서 자른다.
    expression_marker = "Expression"
    if expression_marker in clean_kor:
        cut_index = clean_kor.find(expression_marker)
        clean_kor = clean_kor[:cut_index].strip()
        logging.debug(
            f"{log_prefix} [Clean] Cut at Expression Marker (Index {cut_index})"
        )

    return clean_kor.strip()


def fetch_and_extract_body(url: str, selector: str) -> List[Tuple[str, str]]:
    """
    URL에서 본문을 추출하고 정리된 영단어-한글 해석 쌍 리스트를 반환합니다.
    """
    logging.info("--- [1/3] 웹 페이지 요청 및 텍스트 추출 시작 ---")
    final_matches = []

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "lxml")

        body_container = soup.select_one(selector)

        if body_container:
            raw_text = " ".join(body_container.stripped_strings)
            full_text = re.sub(r"\s+", " ", raw_text).strip()

            # 'Expression ]' 섹션 이후만 사용하도록 필터링
            parts = full_text.split("Expression ]")
            vocabulary_text = " ".join([part.strip() for part in parts[1:]])

            # 후반부 불필요한 섹션 경계 제거
            vocabulary_text = vocabulary_text.split("idiom package")[0].strip()
            vocabulary_text = re.split(r"-{10,}", vocabulary_text)[0].strip()
            vocabulary_text = vocabulary_text.split(
                "NEWS COVERAGE FROM THE NEW YORK TIMES"
            )[0].strip()

            # --- 표준 패턴 추출 및 클리닝 ---
            matches_bullet = WORD_PATTERN.findall(vocabulary_text)

            for i, (eng, raw_kor) in enumerate(matches_bullet):
                log_prefix = f"[Voca {i+1:02d}] Eng: '{eng.strip()[:10]}...'"

                # 핵심: 한글 해석 클리닝 함수 호출 (여기서 relieve oneself 항목도 final_matches에 추가됨)
                clean_kor = clean_korean_translation(raw_kor, log_prefix, final_matches)

                # 최종 단어 추가 (clean_kor는 노이즈가 제거된 상태)
                final_matches.append((eng.strip(), clean_kor))

            # --- 비-표준 패턴 추출 및 클리닝 (NYT 섹션의 warm and fuzzy, measly 등) ---
            matches_non_bullet = NON_BULLET_WORD_PATTERN.findall(vocabulary_text)

            bullet_engs = {m[0] for m in final_matches}

            for eng, raw_kor in matches_non_bullet:
                if eng.strip() not in bullet_engs and len(eng.strip()) > 2:
                    clean_kor = raw_kor.strip().split("Expression")[0].strip()
                    clean_kor = re.split(r"\d+\.\s*", clean_kor)[0].strip()

                    if not clean_kor.startswith(eng):
                        final_matches.append((eng.strip(), clean_kor))

            logging.info(
                f"--- [1/3] 텍스트 추출 완료. 총 {len(final_matches)}개의 단어 쌍 발견."
            )
            return final_matches
        else:
            logging.error(
                f"Selector '{selector}'를 사용하여 본문 영역을 찾을 수 없습니다."
            )
            return []

    except requests.exceptions.RequestException as e:
        logging.error(f"URL 요청 실패: {e}")
        return []


# --- MySQL DB 저장 로직 ---
def save_vocabulary_to_mysql(
    db_manager: DatabaseManager, vocabulary_list: List[Tuple[str, str]]
):
    """
    단어 목록을 MySQL daily_vocabulary 테이블에 저장합니다.
    (date, english_word)가 중복되면 korean_meaning 및 updated_at을 업데이트합니다.
    """
    if not vocabulary_list:
        logging.info("[2/3] 저장할 단어가 없습니다. DB 작업을 건너뜝니다.")
        return

    logging.info(f"--- [2/3] MySQL DB 저장 시작 (총 {len(vocabulary_list)}개 항목) ---")

    # DB에 저장할 기준 날짜 (YYYY-MM-DD)
    extract_date = datetime.now().strftime("%Y-%m-%d")

    # DDL에 따라, created_at과 updated_at은 DB가 자동 처리합니다.
    # 따라서 쿼리에는 date, english_word, korean_meaning만 전달합니다.
    upsert_query = """
    INSERT INTO daily_vocabulary (date, english_word, korean_meaning)
    VALUES (%s, %s, %s)
    ON DUPLICATE KEY UPDATE
        korean_meaning = VALUES(korean_meaning),
        updated_at = CURRENT_TIMESTAMP;
    """

    data_to_save = []
    for eng, kor in vocabulary_list:
        data_to_save.append((extract_date, eng.strip(), kor.strip()))

    try:
        with db_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                # executemany로 벌크 삽입/업데이트
                affected_rows = cursor.executemany(upsert_query, data_to_save)
                conn.commit()
                logging.info(f"--- [2/3] DB 저장 완료. {affected_rows}개 행 처리됨.")

    except Exception as e:
        logging.error(f"MySQL 저장 중 치명적인 오류 발생: {e}")
        raise


# --- 메인 실행 ---
if __name__ == "__main__":

    # --- 환경 변수 파일 생성 (테스트 환경 시뮬레이션) ---
    # 실제 환경에서는 이 블록을 제거해야 합니다.
    # .env.dev 파일을 생성하고 기본값을 저장합니다.
    # 이 환경 변수는 사용자가 제공한 DDL 환경(dpai)을 가정합니다.
    if not os.path.exists(".env.dev"):
        with open(".env.dev", "w") as f:
            f.write("DB_HOST=localhost\n")
            f.write("DB_PORT=3306\n")
            f.write("DB_USER=root\n")
            f.write("DB_PASSWORD=1234\n")
            f.write("DB_DATABASE=dpai\n")
            logging.warning(
                "로컬 테스트를 위한 '.env.dev' 파일이 생성되었습니다. DB 연결 정보를 확인하세요."
            )

    try:
        # 1. DB 관리자 초기화
        db_manager = DatabaseManager()

        # 2. 크롤링 및 단어 추출
        vocabulary_list = fetch_and_extract_body(ARTICLE_URL, BODY_SELECTOR)

        # 3. DB 저장
        save_vocabulary_to_mysql(db_manager, vocabulary_list)

        # 4. 최종 결과 출력 (선택 사항)
        logging.info("--- [3/3] 최종 추출 결과 ---")
        for i, (eng, kor) in enumerate(vocabulary_list):
            logging.info(f"[{i+1:02d}] 🇺🇸 {eng} | 🇰🇷 {kor}")
        logging.info(f"=============================")

    except Exception as e:
        logging.critical(f"스크립트 실행 중 오류 발생: {e}")

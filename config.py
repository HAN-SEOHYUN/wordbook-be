"""
EBS 모닝스페셜 크롤러 설정 파일

사용법:
    1. DAYS_AGO 값을 변경 (1 = 어제, 2 = 그제, 3 = 3일 전)
    2. python crawler.py 실행
"""

import os
from typing import Dict, Any


# ============================================================
# 날짜 설정
# ============================================================

# 크롤링할 날짜 (며칠 전)
DAYS_AGO: int = 4

# 예시:
# DAYS_AGO = 1  → 어제 날짜 크롤링
# DAYS_AGO = 2  → 그제 날짜 크롤링
# DAYS_AGO = 7  → 7일 전 날짜 크롤링


# ============================================================
# URL 설정
# ============================================================

# EBS 모닝스페셜 게시판 URL
BOARD_URL: str = "https://home.ebs.co.kr/morning/board/6/502387/list?hmpMnuId=101"

# EBS 베이스 URL
BASE_URL: str = "https://home.ebs.co.kr"

# 백엔드 API URL
API_BASE_URL: str = os.getenv("API_BASE_URL", "http://localhost:8000")
API_ENDPOINT: str = f"{API_BASE_URL}/api/v1/vocabulary/"


# ============================================================
# 크롤링 설정
# ============================================================

# 브라우저 헤드리스 모드 (True: 백그라운드, False: 브라우저 표시)
HEADLESS_MODE: bool = True

# HTML 셀렉터
BODY_SELECTOR: str = "div.con_txt"

# 타임아웃 설정 (초)
PAGE_LOAD_TIMEOUT: int = 10
HTTP_TIMEOUT: int = 10


# ============================================================
# 재시도 설정
# ============================================================

# 게시글을 못 찾으면 이전 날짜를 자동으로 시도할지
AUTO_RETRY_PREVIOUS_DATE: bool = False

# 최대 재시도 일수
MAX_RETRY_DAYS: int = 7


# ============================================================
# 로깅 설정
# ============================================================

LOG_LEVEL: str = "INFO"
LOG_FORMAT: str = "[%(asctime)s] %(levelname)s: %(message)s"
LOG_DATE_FORMAT: str = "%Y-%m-%d %H:%M:%S"


# ============================================================
# 데이터베이스 저장 방식
# ============================================================

# True: DB 직접 저장, False: API 사용
DIRECT_DB_SAVE: bool = False


# ============================================================
# 설정 검증 함수
# ============================================================


def validate_config() -> None:
    """설정 값 유효성 검증"""
    if DAYS_AGO < 1:
        raise ValueError(f"DAYS_AGO는 1 이상이어야 합니다. 현재: {DAYS_AGO}")

    if DAYS_AGO > 365:
        raise ValueError(f"DAYS_AGO는 365 이하여야 합니다. 현재: {DAYS_AGO}")

    if PAGE_LOAD_TIMEOUT < 1:
        raise ValueError(f"PAGE_LOAD_TIMEOUT은 1 이상이어야 합니다.")

    if HTTP_TIMEOUT < 1:
        raise ValueError(f"HTTP_TIMEOUT은 1 이상이어야 합니다.")

    if LOG_LEVEL not in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
        raise ValueError(f"LOG_LEVEL이 올바르지 않습니다: {LOG_LEVEL}")


def print_config() -> None:
    """현재 설정 출력"""
    print("=" * 60)
    print("크롤러 설정")
    print("=" * 60)
    print(f"대상 날짜: {DAYS_AGO}일 전")
    print(f"API URL: {API_ENDPOINT}")
    print(f"Headless 모드: {HEADLESS_MODE}")
    print(f"자동 재시도: {AUTO_RETRY_PREVIOUS_DATE}")
    if AUTO_RETRY_PREVIOUS_DATE:
        print(f"   └─ 최대 {MAX_RETRY_DAYS}일 전까지 시도")
    print(f"저장 방식: {'DB 직접' if DIRECT_DB_SAVE else 'API 사용'}")
    print(f"로그 레벨: {LOG_LEVEL}")
    print("=" * 60)


# 모듈 로드 시 자동 검증
if __name__ != "__main__":
    try:
        validate_config()
    except ValueError as e:
        print(f"❌ [ERROR] 설정 오류: {e}")
        raise

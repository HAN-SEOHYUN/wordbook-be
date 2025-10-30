"""
크롤러 및 시험 관리 스케줄러

크롤러:
- EBS 모닝스페셜: 화, 수, 목 지정 시간에 실행 (전일 데이터 수집)
- BBC Learning English: 월요일 지정 시간에 실행 (전주 목요일 데이터 수집)

시험 관리:
- 월요일 00:00: test_week_info 생성 (이번주 주차 정보)
- 금요일 00:00: test_words 생성 (내일 토요일 시험 단어 30개)
"""

import schedule
import time
import logging
from datetime import datetime

import config
from crawler_ebs import EBSMorningCrawler
from crawler_bbc import BBCLearningEnglishCrawler
from core.test_week_creator import TestWeekCreator
from core.test_words_creator import TestWordsCreator

# 로깅 설정
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format=config.LOG_FORMAT,
    datefmt=config.LOG_DATE_FORMAT,
)
logger = logging.getLogger(__name__)


def run_ebs_crawler():
    """EBS 모닝스페셜 크롤러 실행 (화, 수, 목만)"""
    today = datetime.now()
    weekday = today.weekday()  # 0=월, 1=화, 2=수, 3=목, 4=금, 5=토, 6=일

    # 화(1), 수(2), 목(3)만 실행
    if weekday in [1, 2, 3]:
        logger.info("=" * 80)
        logger.info(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] EBS 크롤러 스케줄 실행")
        logger.info("=" * 80)

        try:
            crawler = EBSMorningCrawler()
            crawler.run()
        except Exception as e:
            logger.error(f"EBS 크롤러 실행 중 에러: {e}", exc_info=True)
    else:
        logger.info(
            f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] "
            f"오늘은 EBS 크롤링 실행일이 아닙니다. (요일: {['월', '화', '수', '목', '금', '토', '일'][weekday]})"
        )


def run_bbc_crawler():
    """BBC Learning English 크롤러 실행 (월요일만)"""
    today = datetime.now()
    weekday = today.weekday()  # 0=월, 1=화, 2=수, 3=목, 4=금, 5=토, 6=일

    # 월요일(0)만 실행
    if weekday == 0:
        logger.info("=" * 80)
        logger.info(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] BBC 크롤러 스케줄 실행")
        logger.info("=" * 80)

        try:
            crawler = BBCLearningEnglishCrawler()
            crawler.run()
            crawler.close()
        except Exception as e:
            logger.error(f"BBC 크롤러 실행 중 에러: {e}", exc_info=True)
    else:
        logger.info(
            f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] "
            f"오늘은 BBC 크롤링 실행일이 아닙니다. (요일: {['월', '화', '수', '목', '금', '토', '일'][weekday]})"
        )


def run_create_week_info():
    """시험 주차 정보 생성 (월요일만)"""
    today = datetime.now()
    weekday = today.weekday()  # 0=월, 1=화, 2=수, 3=목, 4=금, 5=토, 6=일

    # 월요일(0)만 실행
    if weekday == 0:
        logger.info("=" * 80)
        logger.info(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 주차 정보 생성 스케줄 실행")
        logger.info("=" * 80)

        try:
            creator = TestWeekCreator()
            result = creator.create_week_info()

            if result:
                logger.info(f"✓ 주차 정보 생성 완료: {result['name']}")
            else:
                logger.info("⚠️ 이미 존재하는 주차입니다.")

        except Exception as e:
            logger.error(f"주차 정보 생성 중 에러: {e}", exc_info=True)
    else:
        logger.info(
            f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] "
            f"오늘은 주차 정보 생성일이 아닙니다. (요일: {['월', '화', '수', '목', '금', '토', '일'][weekday]})"
        )


def run_create_test_words():
    """시험 단어 목록 생성 (금요일만)"""
    today = datetime.now()
    weekday = today.weekday()  # 0=월, 1=화, 2=수, 3=목, 4=금, 5=토, 6=일

    # 금요일(4)만 실행
    if weekday == 4:
        logger.info("=" * 80)
        logger.info(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 시험 단어 생성 스케줄 실행")
        logger.info("=" * 80)

        try:
            creator = TestWordsCreator()
            result = creator.create_test_words()

            if result:
                logger.info(f"✓ 시험 단어 생성 완료: {result['name']} ({result['word_count']}개)")
            else:
                logger.error("❌ 시험 단어 생성 실패")

        except Exception as e:
            logger.error(f"시험 단어 생성 중 에러: {e}", exc_info=True)
    else:
        logger.info(
            f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] "
            f"오늘은 시험 단어 생성일이 아닙니다. (요일: {['월', '화', '수', '목', '금', '토', '일'][weekday]})"
        )


def setup_schedule():
    """스케줄 설정"""

    # BBC 크롤러: 매일 지정 시간에 실행 (함수 내부에서 월요일 체크)
    bbc_time = f"{config.BBC_HOUR:02d}:{config.BBC_MINUTE:02d}"
    schedule.every().day.at(bbc_time).do(run_bbc_crawler)
    logger.info(f"✓ BBC 크롤러 스케줄 등록: 매일 {bbc_time} (월요일만 실행)")

    # EBS 크롤러: 매일 지정 시간에 실행 (함수 내부에서 화,수,목 체크)
    ebs_time = f"{config.EBS_HOUR:02d}:{config.EBS_MINUTE:02d}"
    schedule.every().day.at(ebs_time).do(run_ebs_crawler)
    logger.info(f"✓ EBS 크롤러 스케줄 등록: 매일 {ebs_time} (화,수,목만 실행)")

    # 주차 정보 생성: 매일 00:00 (함수 내부에서 월요일 체크)
    schedule.every().day.at("00:00").do(run_create_week_info)
    logger.info(f"✓ 주차 정보 생성 스케줄 등록: 매일 00:00 (월요일만 실행)")

    # 시험 단어 생성: 매일 00:00 (함수 내부에서 금요일 체크)
    schedule.every().day.at("00:00").do(run_create_test_words)
    logger.info(f"✓ 시험 단어 생성 스케줄 등록: 매일 00:00 (금요일만 실행)")


def main():
    """메인 함수"""
    logger.info("=" * 80)
    logger.info("크롤러 스케줄러 시작")
    logger.info("=" * 80)

    # 설정 검증
    try:
        config.validate_config()
    except ValueError as e:
        logger.error(f"설정 오류: {e}")
        return

    # 설정 출력
    config.print_config()

    # 스케줄 설정
    setup_schedule()

    logger.info("=" * 80)
    logger.info("스케줄러가 실행 중입니다. (Ctrl+C로 종료)")
    logger.info("=" * 80)

    # 스케줄 실행 루프
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # 1분마다 체크
    except KeyboardInterrupt:
        logger.info("\n스케줄러 종료")


if __name__ == "__main__":
    main()

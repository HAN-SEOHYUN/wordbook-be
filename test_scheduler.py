"""
스케줄러 테스트 스크립트

스케줄 등록이 정상적으로 작동하는지 테스트합니다.
"""

import config
from scheduler import setup_schedule
import schedule
import logging

# 로깅 설정
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format=config.LOG_FORMAT,
    datefmt=config.LOG_DATE_FORMAT,
)
logger = logging.getLogger(__name__)


def test_scheduler():
    """스케줄러 테스트"""
    logger.info("=" * 80)
    logger.info("스케줄러 테스트 시작")
    logger.info("=" * 80)

    # 설정 검증
    try:
        config.validate_config()
        logger.info("✓ 설정 검증 완료")
    except ValueError as e:
        logger.error(f"✗ 설정 오류: {e}")
        return

    # 설정 출력
    config.print_config()

    # 스케줄 설정
    logger.info("\n스케줄 등록 중...")
    setup_schedule()

    # 등록된 스케줄 확인
    logger.info("\n등록된 스케줄 목록:")
    for job in schedule.get_jobs():
        logger.info(f"  - {job}")

    logger.info("\n=" * 80)
    logger.info("✅ 스케줄러 테스트 완료!")
    logger.info("=" * 80)


if __name__ == "__main__":
    test_scheduler()

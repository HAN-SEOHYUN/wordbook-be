-- ============================================================
-- Migration: Add test_start_datetime and test_end_datetime columns
-- Description: 시험 시간을 관리하기 위한 datetime 컬럼 추가
-- Date: 2025-10-30
-- ============================================================

-- 1. 컬럼 추가
ALTER TABLE `test_week_info`
  ADD COLUMN `test_start_datetime` DATETIME NULL COMMENT '시험 시작 시간 (토요일 10:10)' AFTER `end_date`,
  ADD COLUMN `test_end_datetime` DATETIME NULL COMMENT '시험 종료 시간 (토요일 10:25)' AFTER `test_start_datetime`;

-- 2. 인덱스 추가
ALTER TABLE `test_week_info`
  ADD KEY `idx_test_week_info_test_datetime` (`test_start_datetime`, `test_end_datetime`);

-- 3. 기존 데이터 마이그레이션
-- 각 주차의 start_date 기준으로 해당 주의 토요일을 찾아 시험 시간 설정
UPDATE `test_week_info`
SET
  `test_start_datetime` = DATE_ADD(
    DATE_ADD(`end_date`, INTERVAL (6 - DAYOFWEEK(`end_date`)) DAY),
    INTERVAL 10 * 3600 + 10 * 60 SECOND
  ),
  `test_end_datetime` = DATE_ADD(
    DATE_ADD(`end_date`, INTERVAL (6 - DAYOFWEEK(`end_date`)) DAY),
    INTERVAL 10 * 3600 + 25 * 60 SECOND
  )
WHERE `test_start_datetime` IS NULL;

-- 4. NOT NULL 제약조건 추가
ALTER TABLE `test_week_info`
  MODIFY COLUMN `test_start_datetime` DATETIME NOT NULL COMMENT '시험 시작 시간 (토요일 10:10)',
  MODIFY COLUMN `test_end_datetime` DATETIME NOT NULL COMMENT '시험 종료 시간 (토요일 10:25)';

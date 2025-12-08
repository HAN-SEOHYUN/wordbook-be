-- ============================================
-- 최적화된 DDL - DB 관계 및 성능 최적화
-- ============================================

-- sb.users definition
-- 독립 테이블: 다른 테이블이 참조

CREATE TABLE `users` (
  `U_ID` int NOT NULL AUTO_INCREMENT COMMENT 'PK: 사용자 ID',
  `USERNAME` varchar(150) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '사용자명',
  `CREATED_AT` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '생성일시',
  `UPDATED_AT` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '수정일시',
  PRIMARY KEY (`U_ID`),
  UNIQUE KEY `uk_users_username` (`USERNAME`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='사용자 테이블';

-- sb.word_book definition
-- 독립 테이블: test_words가 참조
-- 최적화: date 인덱스 추가 (ORDER BY date DESC 쿼리 최적화)

CREATE TABLE `word_book` (
  `WB_ID` int NOT NULL AUTO_INCREMENT COMMENT 'PK: 단어 ID',
  `DATE` date NOT NULL COMMENT '단어 추출 날짜',
  `WORD_ENGLISH` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '영단어 또는 구문',
  `WORD_MEANING` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '해석',
  `SOURCE_URL` varchar(1024) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '단어 출처 URL',
  `CREATED_AT` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '생성일시',
  `UPDATED_AT` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '마지막 업데이트 일시',
  PRIMARY KEY (`WB_ID`),
  UNIQUE KEY `uk_date_word` (`DATE`,`WORD_ENGLISH`),
  KEY `idx_word_book_date` (`DATE` DESC) COMMENT '날짜별 조회 및 정렬 최적화'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='일일 어휘 추출 결과 저장 테이블';

-- sb.test_week_info definition
-- 독립 테이블: test_result와 test_words가 참조
-- 최적화: 날짜 범위 조회를 위한 복합 인덱스 개선

CREATE TABLE `test_week_info` (
  `TWI_ID` int NOT NULL AUTO_INCREMENT COMMENT 'PK: 시험 주차 ID',
  `NAME` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '주차명 (예: 2025-10-2주차)',
  `START_DATE` date NOT NULL COMMENT '주차 시작일',
  `END_DATE` date NOT NULL COMMENT '주차 종료일',
  `TEST_START_DATETIME` datetime NOT NULL COMMENT '시험 시작 시간 (토요일 10:10)',
  `TEST_END_DATETIME` datetime NOT NULL COMMENT '시험 종료 시간 (토요일 10:25)',
  `CREATED_AT` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '생성일시',
  `UPDATED_AT` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '수정일시',
  PRIMARY KEY (`TWI_ID`),
  UNIQUE KEY `uk_test_week_info_name` (`NAME`),
  UNIQUE KEY `uk_test_week_info_start_date` (`START_DATE`),
  KEY `idx_test_week_info_dates` (`START_DATE`,`END_DATE`) COMMENT '날짜 범위 조회 최적화',
  KEY `idx_test_week_info_test_datetime` (`TEST_START_DATETIME`,`TEST_END_DATETIME`) COMMENT '시험 시간 범위 조회 최적화'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='시험 주차 정의 테이블';

-- sb.test_result definition
-- users와 test_week_info를 참조
-- 최적화: 
-- 1. UNIQUE KEY가 (U_ID, TWI_ID)이므로 U_ID 단독 인덱스는 중복 제거
-- 2. TEST_SCORE IS NOT NULL 필터링을 위한 인덱스 추가
-- 3. 커버링 인덱스 고려 (자주 조회되는 컬럼 포함)

CREATE TABLE `test_result` (
  `TR_ID` int NOT NULL AUTO_INCREMENT COMMENT 'PK: 주차별 시험 ID',
  `U_ID` int NOT NULL COMMENT 'FK: 사용자 ID (users.U_ID)',
  `TWI_ID` int NOT NULL COMMENT 'FK: 시험 주차 ID (test_week_info.TWI_ID)',
  `TEST_SCORE` int DEFAULT NULL COMMENT '테스트 점수 (NULL=미완료, 정수값=완료)',
  `CREATED_AT` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '생성일시',
  `UPDATED_AT` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '수정일시',
  PRIMARY KEY (`TR_ID`),
  UNIQUE KEY `uk_test_result_user_week` (`U_ID`,`TWI_ID`),
  KEY `idx_test_result_twi_id` (`TWI_ID`),
  KEY `idx_test_result_u_id_created` (`U_ID`,`CREATED_AT` DESC) COMMENT '사용자별 시험 기록 조회 최적화',
  KEY `idx_test_result_u_id_score` (`U_ID`,`TEST_SCORE`) COMMENT '사용자별 완료된 시험 조회 최적화 (TEST_SCORE IS NOT NULL)',
  CONSTRAINT `fk_test_result_twi_id` FOREIGN KEY (`TWI_ID`) REFERENCES `test_week_info` (`TWI_ID`) ON DELETE CASCADE,
  CONSTRAINT `fk_test_result_u_id` FOREIGN KEY (`U_ID`) REFERENCES `users` (`U_ID`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='사용자의 주차별 시험 기록 (재시험 시 덮어쓰기)';

-- sb.test_words definition
-- test_week_info와 word_book을 참조
-- 최적화: UNIQUE KEY가 (TWI_ID, WB_ID)이므로 TWI_ID 단독 인덱스는 중복 제거 가능하나
--        JOIN 쿼리 최적화를 위해 유지 (외래키 인덱스와 별도로 최적화)

CREATE TABLE `test_words` (
  `TW_ID` int NOT NULL AUTO_INCREMENT COMMENT 'PK: 주차별 단어 ID',
  `TWI_ID` int NOT NULL COMMENT 'FK: 시험 주차 ID (test_week_info.TWI_ID)',
  `WB_ID` int NOT NULL COMMENT 'FK: 원본 단어 ID (word_book.WB_ID)',
  `CREATED_AT` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '생성일시',
  `UPDATED_AT` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '수정일시',
  PRIMARY KEY (`TW_ID`),
  UNIQUE KEY `uk_test_words_week_word` (`TWI_ID`,`WB_ID`),
  KEY `idx_test_words_twi_id` (`TWI_ID`) COMMENT '주차별 단어 조회 최적화',
  KEY `idx_test_words_wb_id` (`WB_ID`) COMMENT '단어별 시험 조회 최적화',
  CONSTRAINT `fk_test_words_twi_id` FOREIGN KEY (`TWI_ID`) REFERENCES `test_week_info` (`TWI_ID`) ON DELETE CASCADE,
  CONSTRAINT `fk_test_words_wb_id` FOREIGN KEY (`WB_ID`) REFERENCES `word_book` (`WB_ID`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='주차별 시험 단어 목록 (word_book 참조)';

-- sb.test_answers definition
-- test_result와 test_words를 참조
-- 최적화:
-- 1. UNIQUE KEY가 (TR_ID, TW_ID)이므로 TR_ID 단독 인덱스는 중복 제거 가능
-- 2. IS_CORRECT 집계를 위한 복합 인덱스 개선
-- 3. JOIN 쿼리 최적화를 위한 인덱스 유지

CREATE TABLE `test_answers` (
  `TA_ID` int NOT NULL AUTO_INCREMENT COMMENT 'PK: 문항별 답안 ID',
  `TR_ID` int NOT NULL COMMENT 'FK: 주차별 시험 ID (test_result.TR_ID)',
  `TW_ID` int NOT NULL COMMENT 'FK: 주차별 단어 ID (test_words.TW_ID)',
  `USER_ANSWER` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '사용자 입력 답안',
  `IS_CORRECT` tinyint(1) NOT NULL DEFAULT '0' COMMENT '정답 여부 (1=정답, 0=오답)',
  `CREATED_AT` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '생성일시',
  `UPDATED_AT` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '수정일시',
  PRIMARY KEY (`TA_ID`),
  UNIQUE KEY `uk_test_answers_test_word` (`TR_ID`,`TW_ID`),
  KEY `idx_test_answers_tw_id` (`TW_ID`) COMMENT '단어별 답안 조회 최적화',
  KEY `idx_test_answers_tr_id_correct` (`TR_ID`,`IS_CORRECT`) COMMENT '시험별 정답/오답 집계 최적화',
  CONSTRAINT `fk_test_answers_tr_id` FOREIGN KEY (`TR_ID`) REFERENCES `test_result` (`TR_ID`) ON DELETE CASCADE,
  CONSTRAINT `fk_test_answers_tw_id` FOREIGN KEY (`TW_ID`) REFERENCES `test_words` (`TW_ID`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='주차별 시험 내 문항별 사용자 답안 기록';

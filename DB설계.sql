 -- ============================================================
  -- 0. 일일 어휘 테이블 (원본 단어)
  -- ============================================================
  CREATE TABLE `word_book` (
    `wb_id` INT NOT NULL AUTO_INCREMENT COMMENT 'PK: 단어장 ID',
    `date` DATE NOT NULL COMMENT '단어 추출 날짜',
    `word_english` VARCHAR(216) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '영단어 또는 구문',
    `word_meaning` TEXT COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '한글 의미',
    `source_url` VARCHAR(1024) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '단어 출처 URL',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '생성일시',
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '수정일시',
    PRIMARY KEY (`wb_id`),
    UNIQUE KEY `uk_word_book_date_english` (`date`, `word_english`),
    KEY `idx_word_book_date` (`date`)
  ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='일일 어휘 추출 결과 저장 테이블';

  -- ============================================================
  -- 1. 사용자 테이블
  -- ============================================================
  CREATE TABLE `users` (
    `u_id` INT NOT NULL AUTO_INCREMENT COMMENT 'PK: 사용자 ID',
    `username` VARCHAR(150) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '사용자명',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '생성일시',
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '수정일시',
    PRIMARY KEY (`u_id`),
    UNIQUE KEY `uk_users_username` (`username`)
  ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='사용자 테이블';

  -- ============================================================
  -- 2. 시험 주차 테이블
  -- ============================================================
  CREATE TABLE `test_week_info` (
    `twi_id` INT NOT NULL AUTO_INCREMENT COMMENT 'PK: 시험 주차 ID',
    `name` VARCHAR(100) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '주차명 (예: 2025-10-2주차)',
    `start_date` DATE NOT NULL COMMENT '주차 시작일',
    `end_date` DATE NOT NULL COMMENT '주차 종료일',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '생성일시',
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '수정일시',
    PRIMARY KEY (`twi_id`),
    UNIQUE KEY `uk_test_week_info_name` (`name`),
    UNIQUE KEY `uk_test_week_info_start_date` (`start_date`),
    KEY `idx_test_week_info_dates` (`start_date`, `end_date`)
  ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='시험 주차 정의 테이블';

  -- ============================================================
  -- 3. 주차별 단어 테이블 (시험 문제 세트 - 원본 참조 방식)
  -- ============================================================
  CREATE TABLE `test_words` (
    `tw_id` INT NOT NULL AUTO_INCREMENT COMMENT 'PK: 주차별 단어 ID',
    `twi_id` INT NOT NULL COMMENT 'FK: 시험 주차 ID (test_week_info.twi_id)',
    `wb_id` INT NOT NULL COMMENT 'FK: 원본 단어 ID (word_book.wb_id)',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '생성일시',
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '수정일시',
    PRIMARY KEY (`tw_id`),
    UNIQUE KEY `uk_test_words_week_word` (`twi_id`, `wb_id`),
    KEY `idx_test_words_twi_id` (`twi_id`),
    KEY `idx_test_words_wb_id` (`wb_id`),
    CONSTRAINT `fk_test_words_twi_id` FOREIGN KEY (`twi_id`) REFERENCES `test_week_info` (`twi_id`) ON DELETE
  CASCADE,
    CONSTRAINT `fk_test_words_wb_id` FOREIGN KEY (`wb_id`) REFERENCES `word_book` (`wb_id`) ON DELETE CASCADE
  ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='주차별 시험 단어 목록 (word_book
  참조)';

  -- ============================================================
  -- 4. 주차별 시험 기록 (1주차 1회, 재시험 시 덮어쓰기)
  -- ============================================================
  CREATE TABLE `test_result` (
    `tr_id` INT NOT NULL AUTO_INCREMENT COMMENT 'PK: 주차별 시험 ID',
    `u_id` INT NOT NULL COMMENT 'FK: 사용자 ID (users.u_id)',
    `twi_id` INT NOT NULL COMMENT 'FK: 시험 주차 ID (test_week_info.twi_id)',
    `test_score` INT DEFAULT NULL COMMENT '테스트 점수 (NULL=미완료, 정수값=완료)',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '생성일시',
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '수정일시',
    PRIMARY KEY (`tr_id`),
    UNIQUE KEY `uk_test_result_user_week` (`u_id`, `twi_id`),
    KEY `idx_test_result_u_id` (`u_id`),
    KEY `idx_test_result_twi_id` (`twi_id`),
    KEY `idx_test_result_u_id_created` (`u_id`, `created_at` DESC),
    CONSTRAINT `fk_test_result_u_id` FOREIGN KEY (`u_id`) REFERENCES `users` (`u_id`) ON DELETE CASCADE,
    CONSTRAINT `fk_test_result_twi_id` FOREIGN KEY (`twi_id`) REFERENCES `test_week_info` (`twi_id`) ON DELETE
  CASCADE
  ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='사용자의 주차별 시험 기록 (재시험 시
  덮어쓰기)';

  -- ============================================================
  -- 5. 주차별 시험 문항 답안
  -- ============================================================
  CREATE TABLE `test_answers` (
    `ta_id` INT NOT NULL AUTO_INCREMENT COMMENT 'PK: 문항별 답안 ID',
    `tr_id` INT NOT NULL COMMENT 'FK: 주차별 시험 ID (test_result.tr_id)',
    `tw_id` INT NOT NULL COMMENT 'FK: 주차별 단어 ID (test_words.tw_id)',
    `user_answer` TEXT COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '사용자 입력 답안',
    `is_correct` TINYINT(1) NOT NULL DEFAULT 0 COMMENT '정답 여부 (1=정답, 0=오답)',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '생성일시',
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '수정일시',
    PRIMARY KEY (`ta_id`),
    UNIQUE KEY `uk_test_answers_test_word` (`tr_id`, `tw_id`),
    KEY `idx_test_answers_tr_id` (`tr_id`),
    KEY `idx_test_answers_tw_id` (`tw_id`),
    KEY `idx_test_answers_tr_id_correct` (`tr_id`, `is_correct`),
    CONSTRAINT `fk_test_answers_tr_id` FOREIGN KEY (`tr_id`) REFERENCES `test_result` (`tr_id`) ON DELETE CASCADE,
    CONSTRAINT `fk_test_answers_tw_id` FOREIGN KEY (`tw_id`) REFERENCES `test_words` (`tw_id`) ON DELETE CASCADE
  ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='주차별 시험 내 문항별 사용자 답안
  기록';
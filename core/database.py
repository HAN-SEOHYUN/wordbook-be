import pymysql
import pymysql.cursors
from contextlib import contextmanager
import logging
import os
from dotenv import load_dotenv

# 환경 변수를 .env.dev 파일에서 로드
load_dotenv(".env.dev")


class DatabaseManager:
    """환경 변수를 통해 MySQL 연결 정보를 관리하고 커넥션을 제공하는 클래스입니다."""

    def __init__(self):
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
                f"Required environment variable {e} is not set. Check the .env.dev file."
            )
            raise

        # 2. DB_PORT (기본값: 3306)
        try:
            port_str = os.getenv("DB_PORT", "3306")
            self.port = int(port_str)
        except ValueError:
            logging.error(
                f"DB_PORT environment variable ({port_str}) is not a valid number. Using 3306."
            )
            self.port = 3306

        logging.info("DatabaseManager initialized successfully.")

    @contextmanager
    def get_connection(self):
        """Generates and manages a MySQL connection using context manager."""
        connection = None
        try:
            connection = pymysql.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                database=self.database,
                charset="utf8mb4",
                cursorclass=pymysql.cursors.DictCursor,  # 결과를 딕셔너리로 반환
                autocommit=False,  # 트랜잭션 수동 관리
                init_command="SET time_zone='+09:00'",
            )
            yield connection
        except Exception as e:
            if connection:
                connection.rollback()
            logging.error(f"Database error during transaction: {e}")
            raise  # 예외를 호출자에게 다시 던짐
        finally:
            if connection:
                connection.close()

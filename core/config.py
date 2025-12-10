import sys
import logging
from pathlib import Path
from dotenv import load_dotenv

# 상위 디렉토리(be)를 sys.path에 추가하여 config.py를 import 할 수 있게 함
# (이미 패키지 구조상 import가 가능할 수도 있지만, 안전하게 경로 추가)
current_dir = Path(__file__).resolve().parent  # be/core
be_dir = current_dir.parent  # be
sys.path.append(str(be_dir))

try:
    from config import ENV_ENVIRONMENT
except ImportError:
    # config.py를 찾지 못할 경우 기본값 설정 (Fallback)
    logging.warning("Output: Warning: Could not import ENV_ENVIRONMENT from be.config. Using default 'local'.")
    ENV_ENVIRONMENT = "local"


class Settings:
    def __init__(self):
        # be/config.py에서 정의한 ENV_ENVIRONMENT 값을 사용
        self.env = ENV_ENVIRONMENT
        self._load_env_file()

    def _load_env_file(self):
        """환경 변수(ENV)에 따라 적절한 .env 파일을 로드합니다."""
        base_dir = Path(__file__).resolve().parent.parent
        
        # ENV 값에 따른 파일명 매핑
        filename = f".env.{self.env}"
        env_path = base_dir / filename

        # 파일이 존재하면 로드 (override=False: 시스템 환경 변수 우선)
        if env_path.exists():
            load_dotenv(env_path, override=False)
            logging.info(f"Loaded environment from {filename} (ENV={self.env})")
        else:
            logging.warning(f"Environment file {filename} not found. Using system environment variables.")

settings = Settings()

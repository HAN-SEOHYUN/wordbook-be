import logging
from fastapi import FastAPI
from dotenv import load_dotenv
import os

# 환경 변수 로드 (DatabaseManager 초기화에 필요)
# Note: 실제 프로젝트 환경에 따라 .env.dev, .env.prod 등 적절한 파일을 로드해야 함
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env.dev"))

from api.routers import vocabulary as vocabulary_router

# 로깅 설정
logging.basicConfig(level=logging.INFO)

# FastAPI 애플리케이션 생성
app = FastAPI(
    title="Wordbook API",
    description="일일 어휘 크롤링 및 관리 서비스 API",
    version="1.0.0",
)

# API 라우터 등록 및 /api/v1 프리픽스 추가
app.include_router(vocabulary_router.router, prefix="/api/v1")

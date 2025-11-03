from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# 1. api/routers 파일에서 router 객체를 가져옵니다.
from api.routers.vocabulary import router as vocabulary_router
from api.routers.tts import router as tts_router
from api.routers.users import router as users_router
from api.routers.test_weeks import router as test_weeks_router
from api.routers.tests import router as tests_router

# FastAPI 애플리케이션 초기화
app = FastAPI(
    title="Vocabulary API",
    description="일일 영단어 및 구문 관리 시스템 API",
    version="1.0.0",
)

# CORS 설정 추가 (라우터보다 먼저!)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
        "http://192.168.0.65:3000",  # Network 주소
        "http://172.25.80.1:3000",  # Network 주소 (3000)
        "http://172.25.80.1:3001",  # Network 주소 (3001)
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. 라우터 객체를 메인 애플리케이션에 등록합니다.
# '/api/v1' 프리픽스를 사용하여 모든 엔드포인트 URL 앞에 붙여줍니다.
app.include_router(vocabulary_router, prefix="/api/v1")
app.include_router(tts_router, prefix="/api/v1")
app.include_router(users_router, prefix="/api/v1")
app.include_router(test_weeks_router, prefix="/api/v1")
app.include_router(tests_router, prefix="/api/v1")

# 3. Static 파일 서빙 설정 (오디오 캐시 파일 제공)
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/", tags=["Root"])
def read_root():
    return {"message": "Welcome to the Vocabulary API"}


# 기타 설정 (DB 초기화, 이벤트 핸들러 등...)
# ...

from fastapi import APIRouter, Depends, Query, status
from typing import List, Optional, Dict
from core.database import DatabaseManager
from services.vocabulary import VocabularyService
from schemas.vocabulary import VocabularyCreate, VocabularyUpdate, VocabularyResponse

# FastAPI Router 인스턴스 생성
router = APIRouter(
    prefix="/vocabulary",
    tags=["Vocabulary Management"],
)


# Dependency: DatabaseManager 인스턴스를 제공합니다. (전역 스코프에서 초기화 방지)
def get_db_manager() -> DatabaseManager:
    """DatabaseManager 인스턴스를 생성하고 제공합니다."""
    # 초기화는 의존성 시스템 내에서 이루어지므로, 멀티프로세싱 문제를 피할 수 있습니다.
    return DatabaseManager()


# Dependency: VocabularyService 인스턴스를 각 요청에 제공합니다.
def get_vocabulary_service(
    db_manager: DatabaseManager = Depends(get_db_manager),  # Manager 인스턴스에 의존
) -> VocabularyService:
    """VocabularyService 인스턴스를 생성하고 제공합니다."""
    # Service는 초기화된 Manager를 받아서 사용합니다.
    return VocabularyService(db_manager)


# --- CRUD Endpoints ---


@router.post(
    "/",
    response_model=VocabularyResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create or Update a Vocabulary Item (UPSERT)",
)
def create_vocabulary(
    word_data: VocabularyCreate,
    service: VocabularyService = Depends(get_vocabulary_service),
):
    """
    새로운 단어를 생성합니다. (date, english_word)가 중복될 경우 기존 레코드를 업데이트(UPSERT)합니다.
    """
    return service.create_or_update_word(word_data)


@router.get(
    "/{word_id}",
    response_model=VocabularyResponse,
    summary="Get a Vocabulary Item by ID",
)
def get_vocabulary_by_id(
    word_id: int,
    service: VocabularyService = Depends(get_vocabulary_service),
):
    """특정 ID를 가진 단어 정보를 조회합니다."""
    return service.get_word(word_id)


@router.get(
    "/", response_model=List[VocabularyResponse], summary="Get List of Vocabulary Items"
)
def get_vocabulary_list(
    # 쿼리 파라미터 정의
    limit: int = Query(
        100, ge=1, le=500, description="Maximum number of items to return"
    ),
    offset: int = Query(0, ge=0, description="Number of items to skip"),
    target_date: Optional[str] = Query(
        None, description="Filter by specific date (YYYY-MM-DD)"
    ),
    service: VocabularyService = Depends(get_vocabulary_service),
):
    """
    단어 목록을 조회합니다. 날짜 필터링, 페이징(limit/offset)을 지원합니다.
    """
    return service.get_word_list(limit, offset, target_date)


@router.put(
    "/{word_id}",
    response_model=VocabularyResponse,
    summary="Update a Vocabulary Item by ID",
)
def update_vocabulary(
    word_id: int,
    word_data: VocabularyUpdate,
    service: VocabularyService = Depends(get_vocabulary_service),
):
    """특정 ID를 가진 단어의 정보(영단어, 한글 해석)를 업데이트합니다."""
    return service.update_word(word_id, word_data)


@router.delete(
    "/{word_id}",
    response_model=Dict[str, str],
    status_code=status.HTTP_200_OK,
    summary="Delete a Vocabulary Item by ID",
)
def delete_vocabulary(
    word_id: int,
    service: VocabularyService = Depends(get_vocabulary_service),
):
    """특정 ID를 가진 단어를 삭제합니다."""
    return service.delete_word(word_id)

from fastapi import APIRouter, Depends
from core.database import DatabaseManager
from services.users import UserService
from schemas.users import UserListResponse

router = APIRouter(
    prefix="/users",
    tags=["User Management"],
)


def get_db_manager() -> DatabaseManager:
    """DatabaseManager 인스턴스를 생성하고 제공합니다."""
    return DatabaseManager()


def get_user_service(
    db_manager: DatabaseManager = Depends(get_db_manager),
) -> UserService:
    """UserService 인스턴스를 생성하고 제공합니다."""
    return UserService(db_manager)


@router.get(
    "/",
    response_model=UserListResponse,
    summary="Get All Users",
)
def get_users(
    service: UserService = Depends(get_user_service),
):
    """
    모든 사용자 목록을 조회합니다.
    """
    return service.get_all_users()

from fastapi import HTTPException, status
from core.database import DatabaseManager
from schemas.users import UserResponse, UserListResponse
from crud import users as crud_users


class UserService:
    """사용자 관련 비즈니스 로직을 처리하는 서비스 클래스"""

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def get_all_users(self) -> UserListResponse:
        """모든 사용자 목록 조회"""
        try:
            with self.db.get_connection() as conn:
                db_users = crud_users.get_all_users(conn)
                users = [UserResponse(**user) for user in db_users]
                return UserListResponse(users=users)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to fetch users: {e}",
            )

    def get_user_by_id(self, u_id: int) -> UserResponse:
        """특정 사용자 조회"""
        with self.db.get_connection() as conn:
            db_user = crud_users.get_user_by_id(conn, u_id)

            if not db_user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"User with ID {u_id} not found.",
                )
            return UserResponse(**db_user)

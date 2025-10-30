from pydantic import BaseModel
from datetime import datetime

# 응답 모델
class UserResponse(BaseModel):
    u_id: int
    username: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# 목록 응답 모델
class UserListResponse(BaseModel):
    users: list[UserResponse]

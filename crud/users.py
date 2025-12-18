from typing import List, Optional, Dict, Any
from pymysql.connections import Connection

TABLE_NAME = "users"


def get_all_users(conn: Connection) -> List[Dict[str, Any]]:
    """모든 사용자 목록을 조회합니다."""
    sql = f"""
    SELECT 
        U_ID AS u_id, 
        USERNAME AS username, 
        CREATED_AT AS created_at, 
        UPDATED_AT AS updated_at
    FROM {TABLE_NAME}
    ORDER BY U_ID ASC;
    """
    with conn.cursor() as cursor:
        cursor.execute(sql)
        return cursor.fetchall()


def get_user_by_id(conn: Connection, u_id: int) -> Optional[Dict[str, Any]]:
    """ID로 사용자를 조회합니다."""
    sql = f"""
    SELECT 
        U_ID AS u_id, 
        USERNAME AS username, 
        CREATED_AT AS created_at, 
        UPDATED_AT AS updated_at
    FROM {TABLE_NAME}
    WHERE U_ID = %s;
    """
    with conn.cursor() as cursor:
        cursor.execute(sql, (u_id,))
        return cursor.fetchone()

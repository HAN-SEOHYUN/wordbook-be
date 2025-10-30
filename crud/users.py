from typing import List, Optional, Dict, Any
from pymysql.connections import Connection

TABLE_NAME = "users"


def get_all_users(conn: Connection) -> List[Dict[str, Any]]:
    """모든 사용자 목록을 조회합니다."""
    sql = f"""
    SELECT u_id, username, created_at, updated_at
    FROM {TABLE_NAME}
    ORDER BY u_id ASC;
    """
    with conn.cursor() as cursor:
        cursor.execute(sql)
        return cursor.fetchall()


def get_user_by_id(conn: Connection, u_id: int) -> Optional[Dict[str, Any]]:
    """ID로 사용자를 조회합니다."""
    sql = f"""
    SELECT u_id, username, created_at, updated_at
    FROM {TABLE_NAME}
    WHERE u_id = %s;
    """
    with conn.cursor() as cursor:
        cursor.execute(sql, (u_id,))
        return cursor.fetchone()

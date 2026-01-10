"""init rbac data

Revision ID: e2e6e80df912
Revises: df8ee19aa3da
Create Date: 2026-01-09 01:43:08.161728

"""
from typing import Sequence, Union
from datetime import datetime, timezone

from alembic import op
from sqlalchemy import table, column, Integer, String, DateTime, Boolean, Date
from sqlalchemy.sql import select

from app.core.config import settings
from app.core.security import get_password_hash

# revision identifiers, used by Alembic.
revision: str = 'e2e6e80df912'
down_revision: Union[str, Sequence[str], None] = 'df8ee19aa3da'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


sys_admin_user = settings.SYS_ADMIN_USER
sys_admin_init_pwd = settings.SYS_ADMIN_INIT_PWD


def upgrade() -> None:
    """初始化 RBAC 数据：创建角色和系统管理员账号"""
    
    # 定义表结构
    role_table = table(
        'role',
        column('id', Integer),
        column('code', String),
        column('name', String),
        column('created_at', DateTime),
        column('updated_at', DateTime),
    )
    
    user_table = table(
        'user',
        column('id', Integer),
        column('unified_id', String),
        column('password_hash', String),
        column('user_type', String),
        column('is_active', Boolean),
        column('name', String),
        column('gender', String),
        column('birthdate', Date),
        column('created_at', DateTime),
        column('updated_at', DateTime),
    )
    
    user_role_table = table(
        'user_role',
        column('user_id', Integer),
        column('role_id', Integer),
        column('created_at', DateTime),
        column('updated_at', DateTime),
    )
    
    # 1. 创建三个基础角色
    roles = [
        {'code': 'admin', 'name': '管理员'},
        {'code': 'teacher', 'name': '教师'},
        {'code': 'student', 'name': '学生'},
    ]
    op.bulk_insert(role_table, roles)
    
    # 2. 创建初始系统管理员账号
    admin_password = get_password_hash(sys_admin_init_pwd)
    admin_user = {
        'unified_id': sys_admin_user,
        'password_hash': admin_password,
        'user_type': 'admin',
        'is_active': True,
        'name': '系统管理员',
        'gender': 'unknown',
    }
    op.bulk_insert(user_table, [admin_user])
    
    # 3. 为管理员账号授予管理员角色
    # 查询刚创建的用户id和角色id
    conn = op.get_bind()
    admin_user_id = conn.execute(
        select(user_table.c.id).where(user_table.c.unified_id == sys_admin_user)
    ).scalar()
    admin_role_id = conn.execute(
        select(role_table.c.id).where(role_table.c.code == 'admin')
    ).scalar()
    
    user_role = {
        'user_id': admin_user_id,
        'role_id': admin_role_id,
    }
    op.bulk_insert(user_role_table, [user_role])


def downgrade() -> None:
    """回滚 RBAC 数据"""
    conn = op.get_bind()
    
    # 定义表结构
    role_table = table('role', column('id', Integer), column('code', String))
    user_table = table('user', column('id', Integer), column('unified_id', String))
    
    # 1. 查询管理员用户id
    admin_user_id = conn.execute(
        select(user_table.c.id).where(user_table.c.unified_id == sys_admin_user)
    ).scalar()
    
    # 2. 如果找到管理员用户，删除其角色关联
    if admin_user_id:
        op.execute(f"DELETE FROM user_role WHERE user_id = {admin_user_id}")
        # 删除管理员账号
        op.execute(f"DELETE FROM user WHERE id = {admin_user_id}")
    
    # 3. 删除角色
    op.execute("DELETE FROM role WHERE code IN ('admin', 'teacher', 'student')")

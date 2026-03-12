"""add user management access

Revision ID: 333a4335c293
Revises: f1f6a4d418f9
Create Date: 2026-03-12 19:36:49.787811

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from app.common.permissions import (
    USER_CREATE_ADMIN,
    USER_DEACTIVATE_ALL,
    USER_DEACTIVATE_SELF,
    USER_READ_ALL,
    USER_READ_SELF,
    USER_UPDATE_ALL,
    USER_UPDATE_SELF,
)


# revision identifiers, used by Alembic.
revision: str = '333a4335c293'
down_revision: Union[str, Sequence[str], None] = 'f1f6a4d418f9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    conn = op.get_bind()
    permission_table = sa.Table("permission", sa.MetaData(), autoload_with=conn)
    role_table = sa.Table("role", sa.MetaData(), autoload_with=conn)
    role_permission_table = sa.Table("role_permission", sa.MetaData(), autoload_with=conn)

    permissions = [
        USER_READ_SELF,
        USER_READ_ALL,
        USER_UPDATE_SELF,
        USER_UPDATE_ALL,
        USER_DEACTIVATE_SELF,
        USER_DEACTIVATE_ALL,
        USER_CREATE_ADMIN,
    ]
    for permission in permissions:
        if not _permission_exists(conn, permission_table, permission.code):
            op.bulk_insert(
                permission_table,
                [{"code": permission.code, "name": permission.name}],
            )

    admin_role_id = _get_role_id(conn, role_table, "admin")
    teacher_role_id = _get_role_id(conn, role_table, "teacher")
    student_role_id = _get_role_id(conn, role_table, "student")

    for role_id, permission in [
        (admin_role_id, USER_READ_SELF),
        (admin_role_id, USER_READ_ALL),
        (admin_role_id, USER_UPDATE_SELF),
        (admin_role_id, USER_UPDATE_ALL),
        (admin_role_id, USER_DEACTIVATE_SELF),
        (admin_role_id, USER_DEACTIVATE_ALL),
        (admin_role_id, USER_CREATE_ADMIN),
        (teacher_role_id, USER_READ_SELF),
        (teacher_role_id, USER_UPDATE_SELF),
        (teacher_role_id, USER_DEACTIVATE_SELF),
        (student_role_id, USER_READ_SELF),
        (student_role_id, USER_UPDATE_SELF),
        (student_role_id, USER_DEACTIVATE_SELF),
    ]:
        permission_id = _get_permission_id(conn, permission_table, permission.code)
        if not _role_permission_exists(conn, role_permission_table, role_id, permission_id):
            op.bulk_insert(
                role_permission_table,
                [{"role_id": role_id, "permission_id": permission_id}],
            )


def downgrade() -> None:
    """Downgrade schema."""
    conn = op.get_bind()
    role_table = sa.Table("role", sa.MetaData(), autoload_with=conn)
    permission_table = sa.Table("permission", sa.MetaData(), autoload_with=conn)
    role_permission_table = sa.Table("role_permission", sa.MetaData(), autoload_with=conn)

    admin_role_id = _get_role_id(conn, role_table, "admin")
    teacher_role_id = _get_role_id(conn, role_table, "teacher")
    student_role_id = _get_role_id(conn, role_table, "student")

    for role_id, permission in [
        (admin_role_id, USER_READ_SELF),
        (admin_role_id, USER_READ_ALL),
        (admin_role_id, USER_UPDATE_SELF),
        (admin_role_id, USER_UPDATE_ALL),
        (admin_role_id, USER_DEACTIVATE_SELF),
        (admin_role_id, USER_DEACTIVATE_ALL),
        (admin_role_id, USER_CREATE_ADMIN),
        (teacher_role_id, USER_READ_SELF),
        (teacher_role_id, USER_UPDATE_SELF),
        (teacher_role_id, USER_DEACTIVATE_SELF),
        (student_role_id, USER_READ_SELF),
        (student_role_id, USER_UPDATE_SELF),
        (student_role_id, USER_DEACTIVATE_SELF),
    ]:
        permission_id = conn.execute(
            sa.select(permission_table.c.id).where(permission_table.c.code == permission.code)
        ).scalar()
        if permission_id is None:
            continue
        conn.execute(
            role_permission_table.delete().where(
                role_permission_table.c.role_id == role_id,
                role_permission_table.c.permission_id == permission_id,
            )
        )

    for permission in [
        USER_READ_SELF,
        USER_READ_ALL,
        USER_UPDATE_SELF,
        USER_UPDATE_ALL,
        USER_DEACTIVATE_SELF,
        USER_DEACTIVATE_ALL,
        USER_CREATE_ADMIN,
    ]:
        permission_id = conn.execute(
            sa.select(permission_table.c.id).where(permission_table.c.code == permission.code)
        ).scalar()
        if permission_id is None:
            continue
        conn.execute(
            permission_table.delete().where(permission_table.c.id == permission_id)
        )


def _get_role_id(conn, role_table, role_code: str) -> int:
    return conn.execute(sa.select(role_table.c.id).where(role_table.c.code == role_code)).scalar_one()


def _get_permission_id(conn, permission_table, permission_code: str) -> int:
    return conn.execute(
        sa.select(permission_table.c.id).where(permission_table.c.code == permission_code)
    ).scalar_one()


def _permission_exists(conn, permission_table, permission_code: str) -> bool:
    return conn.execute(
        sa.select(permission_table.c.id).where(permission_table.c.code == permission_code)
    ).scalar() is not None


def _role_permission_exists(conn, role_permission_table, role_id: int, permission_id: int) -> bool:
    return conn.execute(
        sa.select(role_permission_table.c.role_id).where(
            role_permission_table.c.role_id == role_id,
            role_permission_table.c.permission_id == permission_id,
        )
    ).scalar() is not None

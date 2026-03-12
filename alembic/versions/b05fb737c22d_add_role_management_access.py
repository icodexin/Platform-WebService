"""add role management access

Revision ID: b05fb737c22d
Revises: 333a4335c293
Create Date: 2026-03-13 02:36:42.074375

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from app.common.permissions import ROLE_MANAGE


# revision identifiers, used by Alembic.
revision: str = 'b05fb737c22d'
down_revision: Union[str, Sequence[str], None] = '333a4335c293'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    conn = op.get_bind()
    permission_table = sa.Table("permission", sa.MetaData(), autoload_with=conn)
    role_table = sa.Table("role", sa.MetaData(), autoload_with=conn)
    role_permission_table = sa.Table("role_permission", sa.MetaData(), autoload_with=conn)

    permission_id = conn.execute(
        sa.select(permission_table.c.id).where(permission_table.c.code == ROLE_MANAGE.code)
    ).scalar()
    if permission_id is None:
        op.bulk_insert(
            permission_table,
            [
                {
                    "code": ROLE_MANAGE.code,
                    "name": ROLE_MANAGE.name,
                }
            ],
        )
        permission_id = conn.execute(
            sa.select(permission_table.c.id).where(permission_table.c.code == ROLE_MANAGE.code)
        ).scalar_one()

    admin_role_id = conn.execute(
        sa.select(role_table.c.id).where(role_table.c.code == "admin")
    ).scalar_one()
    binding_exists = conn.execute(
        sa.select(role_permission_table.c.role_id).where(
            role_permission_table.c.role_id == admin_role_id,
            role_permission_table.c.permission_id == permission_id,
        )
    ).scalar()
    if binding_exists is None:
        op.bulk_insert(
            role_permission_table,
            [
                {
                    "role_id": admin_role_id,
                    "permission_id": permission_id,
                }
            ],
        )


def downgrade() -> None:
    """Downgrade schema."""
    conn = op.get_bind()
    permission_table = sa.Table("permission", sa.MetaData(), autoload_with=conn)
    role_permission_table = sa.Table("role_permission", sa.MetaData(), autoload_with=conn)

    permission_id = conn.execute(
        sa.select(permission_table.c.id).where(permission_table.c.code == ROLE_MANAGE.code)
    ).scalar()
    if permission_id is not None:
        conn.execute(
            role_permission_table.delete().where(role_permission_table.c.permission_id == permission_id)
        )
        conn.execute(
            permission_table.delete().where(permission_table.c.id == permission_id)
        )

from sqlalchemy import Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.common.enums import (
    RabbitMQAuthCheckEnum,
    RabbitMQPermissionLevelEnum,
    RabbitMQResourceTypeEnum,
    RabbitMQTagEnum,
)
from app.core.db import Base, TimestampMixin


class RabbitMQPermissionBinding(Base, TimestampMixin):
    """业务权限到 RabbitMQ HTTP 授权规则的映射表。"""

    __tablename__ = "rabbitmq_permission_binding"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    permission_id: Mapped[int] = mapped_column(
        ForeignKey("permission.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
        comment="业务权限ID",
    )
    check_type: Mapped[RabbitMQAuthCheckEnum] = mapped_column(
        Enum(RabbitMQAuthCheckEnum),
        nullable=False,
        comment="对应 RabbitMQ HTTP 认证后端的检查类型",
    )
    vhost_pattern: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        default="*",
        comment="vhost 匹配模式, 使用 shell-style wildcard",
    )
    resource_type: Mapped[RabbitMQResourceTypeEnum | None] = mapped_column(
        Enum(RabbitMQResourceTypeEnum),
        nullable=True,
        comment="资源类型, resource/topic 检查时可用",
    )
    resource_name_pattern: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="exchange/queue 名称匹配模式, 使用 shell-style wildcard",
    )
    permission_level: Mapped[RabbitMQPermissionLevelEnum | None] = mapped_column(
        Enum(RabbitMQPermissionLevelEnum),
        nullable=True,
        comment="RabbitMQ configure/write/read 权限级别",
    )
    routing_key_pattern: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="topic 路由键匹配模式, 使用 AMQP topic wildcard",
    )
    rabbitmq_tag: Mapped[RabbitMQTagEnum | None] = mapped_column(
        Enum(RabbitMQTagEnum),
        nullable=True,
        comment="RabbitMQ 管理标签, 仅 /auth/user 返回使用",
    )

    permission = relationship("Permission", back_populates="rabbitmq_bindings", lazy="selectin")

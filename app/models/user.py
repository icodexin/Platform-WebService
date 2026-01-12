from datetime import date

from sqlalchemy import Date, Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.common.enums import GenderEnum, StudentTypeEnum, UserTypeEnum
from app.core.db import Base, TimestampMixin


class User(Base, TimestampMixin):
    """用户表"""
    __tablename__ = 'user'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    unified_id: Mapped[str] = mapped_column(
        String(32), unique=True, index=True, comment="统一身份ID, 学号/教工号"
    )
    password_hash: Mapped[str] = mapped_column(
        String(128), nullable=False, comment="密码哈希"
    )
    user_type: Mapped[UserTypeEnum] = mapped_column(
        Enum(UserTypeEnum), nullable=False, comment="用户类型"
    )
    is_active: Mapped[bool] = mapped_column(
        nullable=False, default=True, comment="是否有效账号"
    )

    name: Mapped[str] = mapped_column(
        String(64), nullable=False, comment="姓名"
    )
    gender: Mapped[GenderEnum | None] = mapped_column(
        Enum(GenderEnum), nullable=True, comment="性别"
    )
    birthdate: Mapped[date | None] = mapped_column(
        Date, nullable=True, comment="出生日期"
    )

    student_profile = relationship(
        "StudentProfile", uselist=False, cascade="all, delete-orphan", back_populates="user",
        lazy="selectin"
    )
    teacher_profile = relationship(
        "TeacherProfile", uselist=False, cascade="all, delete-orphan", back_populates="user",
        lazy="selectin"
    )

    roles = relationship(
        "Role", secondary="user_role", back_populates="users", lazy="selectin"
    )


class StudentProfile(Base, TimestampMixin):
    """学生详情表"""
    __tablename__ = 'student_profile'

    user_id: Mapped[int] = mapped_column(
        ForeignKey("user.id", ondelete="CASCADE"), primary_key=True
    )
    student_type: Mapped[StudentTypeEnum] = mapped_column(
        Enum(StudentTypeEnum), nullable=False, comment="学生类型"
    )
    college: Mapped[str | None] = mapped_column(
        String(128), nullable=True, comment="学院"
    )
    major: Mapped[str | None] = mapped_column(
        String(128), nullable=True, comment="专业"
    )
    enrollment_year: Mapped[int | None] = mapped_column(
        nullable=True, comment="入学年份"
    )

    user = relationship("User", back_populates="student_profile")


class TeacherProfile(Base, TimestampMixin):
    """教师详情表"""
    __tablename__ = 'teacher_profile'

    user_id: Mapped[int] = mapped_column(
        ForeignKey("user.id", ondelete="CASCADE"), primary_key=True
    )
    department: Mapped[str | None] = mapped_column(
        String(128), nullable=True, comment="系别"
    )
    title: Mapped[str | None] = mapped_column(
        String(128), nullable=True, comment="职称"
    )

    user = relationship("User", back_populates="teacher_profile")

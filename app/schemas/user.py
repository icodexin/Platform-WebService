from datetime import date, datetime
from typing import Annotated, Literal, Optional, Union

from pydantic import BaseModel, Field, field_validator, model_validator

from app.common.enums import GenderEnum, StudentTypeEnum, UserTypeEnum
from app.core.security import get_password_hash


class UserMutationBase(BaseModel):
    @field_validator(
        "unified_id",
        "name",
        "college",
        "major",
        "department",
        "title",
        mode="before",
        check_fields=False,
    )
    @classmethod
    def strip_string(cls, value: str | None):
        """字段验证前去除字符串字段的前后空白"""
        if value is None:
            return value
        return value.strip()


class UserBase(BaseModel):
    user_type: UserTypeEnum
    unified_id: str = Field(..., min_length=1, max_length=32)
    name: str = Field(..., min_length=1, max_length=64)
    gender: Optional[GenderEnum] = None
    birthdate: Optional[date] = None

    model_config = {
        "from_attributes": True,
    }


class UserIn(UserMutationBase, UserBase):
    password_hash: str = Field(..., alias="password")

    @field_validator("password_hash", mode="before")
    @classmethod
    def valid_password(cls, value: str) -> str:
        if not value or len(value) < 6:
            raise ValueError("密码长度不能少于6位")
        # 已经是Hash密码的直接返回
        if value.startswith("$argon2"):
            return value
        return get_password_hash(value)


class StudentProfile(BaseModel):
    student_type: StudentTypeEnum
    college: Optional[str] = Field(default=None, max_length=128)
    major: Optional[str] = Field(default=None, max_length=128)
    enrollment_year: Optional[int] = None

    model_config = {
        "from_attributes": True,
    }


class StudentCreate(UserIn, StudentProfile):
    user_type: Literal[UserTypeEnum.student] = UserTypeEnum.student

    def get_user_data(self) -> dict:
        return self.model_dump(include=UserIn.model_fields.keys())

    def get_profile_data(self) -> dict:
        return self.model_dump(include=StudentProfile.model_fields.keys())


class TeacherProfile(BaseModel):
    department: Optional[str] = Field(default=None, max_length=128)
    title: Optional[str] = Field(default=None, max_length=128)

    model_config = {
        "from_attributes": True,
    }


class TeacherCreate(UserIn, TeacherProfile):
    user_type: Literal[UserTypeEnum.teacher] = UserTypeEnum.teacher

    def get_user_data(self) -> dict:
        return self.model_dump(include=UserIn.model_fields.keys())

    def get_profile_data(self) -> dict:
        return self.model_dump(include=TeacherProfile.model_fields.keys())


class AdminCreate(UserIn):
    user_type: Literal[UserTypeEnum.admin] = UserTypeEnum.admin

    def get_user_data(self) -> dict:
        return self.model_dump(include=UserIn.model_fields.keys())

    def get_profile_data(self) -> dict:
        return {}


UserCreate = Annotated[
    Union[StudentCreate, TeacherCreate, AdminCreate],
    Field(discriminator="user_type"),
]


class UserUpdate(UserMutationBase):
    unified_id: str | None = Field(default=None, min_length=1, max_length=32)
    password_hash: str | None = Field(default=None, alias="password")
    name: str | None = Field(default=None, min_length=1, max_length=64)
    gender: Optional[GenderEnum] = None
    birthdate: Optional[date] = None
    is_active: bool | None = None

    student_type: StudentTypeEnum | None = None
    college: str | None = Field(default=None, max_length=128)
    major: str | None = Field(default=None, max_length=128)
    enrollment_year: int | None = None

    department: str | None = Field(default=None, max_length=128)
    title: str | None = Field(default=None, max_length=128)

    @field_validator("password_hash", mode="before")
    @classmethod
    def valid_password(cls, value: str | None) -> str | None:
        if value is None:
            return value
        if len(value) < 6:
            raise ValueError("密码长度不能少于6位")
        if value.startswith("$argon2"):
            return value
        return get_password_hash(value)

    @model_validator(mode="after")
    def validate_not_empty(self):
        if not self.model_fields_set:
            raise ValueError("至少需要提供一个更新字段")
        return self

    def get_user_data(self) -> dict:
        return self.model_dump(
            include={"unified_id", "password_hash", "name", "gender", "birthdate", "is_active"},
            exclude_unset=True,
        )

    def get_student_profile_data(self) -> dict:
        return self.model_dump(
            include={"student_type", "college", "major", "enrollment_year"},
            exclude_unset=True,
        )

    def get_teacher_profile_data(self) -> dict:
        return self.model_dump(
            include={"department", "title"},
            exclude_unset=True,
        )


class UserOut(UserBase):
    id: int
    is_active: bool
    roles: list[str]
    created_at: datetime
    updated_at: datetime


class StudentResponse(UserOut, StudentProfile):
    user_type: Literal[UserTypeEnum.student] = UserTypeEnum.student


class TeacherResponse(UserOut, TeacherProfile):
    user_type: Literal[UserTypeEnum.teacher] = UserTypeEnum.teacher


class AdminResponse(UserOut):
    user_type: Literal[UserTypeEnum.admin] = UserTypeEnum.admin


UserResponse = Annotated[
    Union[StudentResponse, TeacherResponse, AdminResponse],
    Field(discriminator="user_type"),
]


class UserListResponse(BaseModel):
    items: list[UserResponse]
    total: int
    page: int
    page_size: int


class UserRoleSummary(BaseModel):
    id: int
    code: str
    name: str
    is_system: bool


class UserRoleAssignmentUpdate(BaseModel):
    role_ids: list[int] = Field(default_factory=list)


class UserRoleAssignmentResponse(BaseModel):
    user_id: int
    immutable_role: UserRoleSummary
    roles: list[UserRoleSummary]

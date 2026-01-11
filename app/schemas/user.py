from datetime import date
from typing import Annotated, Literal, Optional, Union

from pydantic import BaseModel, Field, field_validator

from app.common.enum import GenderEnum, StudentTypeEnum, UserTypeEnum
from app.core.security import get_password_hash


class UserBase(BaseModel):
    user_type: UserTypeEnum
    unified_id: str
    name: str
    gender: Optional[GenderEnum] = None
    birthdate: Optional[date] = None


class UserIn(UserBase):
    password_hash: str = Field(..., alias='password')

    @field_validator('password_hash', mode='before')
    @classmethod
    def valid_password(cls, v: str) -> str:
        if not v or len(v) < 6:
            raise ValueError('密码长度不能少于6位')
        # 已经是 hash 的直接放行
        if v.startswith('$argon2'):
            return v
        return get_password_hash(v)


class StudentProfile(BaseModel):
    student_type: StudentTypeEnum
    college: Optional[str] = None
    major: Optional[str] = None
    enrollment_year: Optional[int] = None


class StudentCreate(UserIn, StudentProfile):
    user_type: Literal[UserTypeEnum.student] = UserTypeEnum.student

    def get_user_data(self) -> dict:
        return self.model_dump(include=UserIn.model_fields.keys())

    def get_profile_data(self) -> dict:
        return self.model_dump(include=StudentProfile.model_fields.keys())


class TeacherProfile(BaseModel):
    department: Optional[str] = None
    title: Optional[str] = None


class TeacherCreate(UserIn, TeacherProfile):
    user_type: Literal[UserTypeEnum.teacher] = UserTypeEnum.teacher

    def get_user_data(self) -> dict:
        return self.model_dump(include=UserIn.model_fields.keys())

    def get_profile_data(self) -> dict:
        return self.model_dump(include=TeacherProfile.model_fields.keys())


UserCreate = Annotated[
    Union[StudentCreate, TeacherCreate],
    Field(discriminator='user_type')
]

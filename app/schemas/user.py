import datetime
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

    model_config = {
        "from_attributes": True,
    }


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
    department: Optional[str] = None
    title: Optional[str] = None

    model_config = {
        "from_attributes": True,
    }


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


class UserOut(UserBase):
    is_active: bool


class StudentResponse(UserOut, StudentProfile):
    user_type: Literal[UserTypeEnum.student] = UserTypeEnum.student


class TeacherResponse(UserOut, TeacherProfile):
    user_type: Literal[UserTypeEnum.teacher] = UserTypeEnum.teacher


class AdminResponse(UserOut):
    user_type: Literal[UserTypeEnum.admin] = UserTypeEnum.admin


UserResponse = Annotated[
    Union[StudentResponse, TeacherResponse, AdminResponse],
    Field(discriminator='user_type')
]


if __name__ == '__main__':
    from pydantic import TypeAdapter
    user = {
        "user_type":'student',
        "is_active":True,
        "unified_id":'123456',
        "name":"test",
        "student_type":StudentTypeEnum.undergraduate,
        "college": "CS",
        "major": "AI",
        "enrollment_year": 2021,
        "id": 111,
        "created_at": datetime.datetime(1, 1, 1,1, 1, 1, 1)
    }
    user = TypeAdapter(UserOut).validate_python(user)
    print(user)
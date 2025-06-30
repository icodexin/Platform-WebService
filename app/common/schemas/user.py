from datetime import date, datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel


class StatusEnum(str, Enum):
    Enabled = "ENABLED"
    Disabled = "DISABLED"

class GenderEnum(str, Enum):
    Male = "M"
    Female = "F"
    Unknown = "U"

class StudentTypeEnum(str, Enum):
    Undergraduate = "UNDERGRADUATE"
    Postgraduate = "POSTGRADUATE"
    Doctoral = "DOCTORAL"


class UserBase(BaseModel):
    user_id: str
    name: str
    gender: GenderEnum = GenderEnum.Unknown
    birthdate: Optional[date] = None
    college: Optional[str] = None
    stu_type: Optional[StudentTypeEnum] = None
    grade: Optional[int] = None
    major: Optional[str] = None


class UserCreate(UserBase):
    password: str


class UserResponse(UserBase):
    last_login_at: Optional[datetime] = None
    last_login_ip: Optional[str] = None


class UserInDB(UserBase):
    hashed_password: str
    status: StatusEnum = StatusEnum.Enabled
    last_login_at: Optional[datetime] = None
    last_login_ip: Optional[str] = None
    created_at: datetime
    created_by: str
    updated_at: datetime
    updated_by: str

from enum import Enum

class UserTypeEnum(str, Enum):
    student = "student"
    teacher = "teacher"
    admin = "admin"


class GenderEnum(str, Enum):
    male = "male"
    female = "female"
    unknown = "unknown"


class StudentTypeEnum(str, Enum):
    undergraduate = "undergraduate"
    master = "master"
    phd = "phd"


class TokenTypeEnum(str, Enum):
    access = "access"
    refresh = "refresh"

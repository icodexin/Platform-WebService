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


class RabbitMQAuthCheckEnum(str, Enum):
    user = "user"
    vhost = "vhost"
    resource = "resource"
    topic = "topic"


class RabbitMQPermissionLevelEnum(str, Enum):
    configure = "configure"
    write = "write"
    read = "read"


class RabbitMQResourceTypeEnum(str, Enum):
    exchange = "exchange"
    queue = "queue"
    topic = "topic"


class RabbitMQTagEnum(str, Enum):
    management = "management"
    policymaker = "policymaker"
    monitoring = "monitoring"
    administrator = "administrator"

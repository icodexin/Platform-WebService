from datetime import datetime

from pydantic import BaseModel, Field, field_validator, model_validator


class PermissionMutationBase(BaseModel):
    @field_validator("code", "name", mode="before", check_fields=False)
    @classmethod
    def strip_string(cls, value: str | None):
        """字段验证前去除字符串字段的前后空白"""
        if value is None:
            return value
        return value.strip()


class PermissionCreate(PermissionMutationBase):
    code: str = Field(
        ...,
        min_length=3,
        max_length=64,
        pattern=r"^[a-z][a-z0-9._:-]*$",
        description="权限唯一编码",
    )
    name: str = Field(..., min_length=1, max_length=128, description="权限名称")


class PermissionUpdate(PermissionMutationBase):
    code: str | None = Field(
        default=None,
        min_length=3,
        max_length=64,
        pattern=r"^[a-z][a-z0-9._:-]*$",
        description="权限唯一编码",
    )
    name: str | None = Field(default=None, min_length=1, max_length=128, description="权限名称")

    @model_validator(mode="after")
    def validate_not_empty(self):
        if self.code is None and self.name is None:
            raise ValueError("至少需要提供一个更新字段")
        return self


class PermissionResponse(BaseModel):
    id: int
    code: str
    name: str
    role_count: int  # 关联的角色数量
    is_system: bool  # 是否为系统权限
    created_at: datetime
    updated_at: datetime


class PermissionListResponse(BaseModel):
    items: list[PermissionResponse]
    total: int
    page: int
    page_size: int

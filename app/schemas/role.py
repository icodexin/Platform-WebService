from datetime import datetime

from pydantic import BaseModel, Field, field_validator, model_validator


class RoleMutationBase(BaseModel):
    @field_validator("code", "name", mode="before", check_fields=False)
    @classmethod
    def strip_string(cls, value: str | None):
        if value is None:
            return value
        return value.strip()


class RolePermissionSummary(BaseModel):
    id: int
    code: str
    name: str

    model_config = {
        "from_attributes": True,
    }


class RoleCreate(RoleMutationBase):
    code: str = Field(..., min_length=1, max_length=64)
    name: str = Field(..., min_length=1, max_length=128)
    permission_ids: list[int] = Field(default_factory=list)


class RoleUpdate(RoleMutationBase):
    code: str | None = Field(default=None, min_length=1, max_length=64)
    name: str | None = Field(default=None, min_length=1, max_length=128)
    permission_ids: list[int] | None = None

    @model_validator(mode="after")
    def validate_not_empty(self):
        if not self.model_fields_set:
            raise ValueError("至少需要提供一个更新字段")
        return self


class RoleResponse(BaseModel):
    id: int
    code: str
    name: str
    permissions: list[RolePermissionSummary]
    permission_count: int
    user_count: int
    is_system: bool
    created_at: datetime
    updated_at: datetime


class RoleListResponse(BaseModel):
    items: list[RoleResponse]
    total: int
    page: int
    page_size: int

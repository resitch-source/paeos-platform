"""Pydantic request/response schemas for Enterprise Core (Phase 1)."""

from __future__ import annotations

import uuid

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# --- Auth ---
class LoginRequest(BaseModel):
    tenant_slug: str = Field(min_length=1, max_length=63)
    email: EmailStr
    password: str = Field(min_length=1)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class MeResponse(BaseModel):
    user_id: uuid.UUID
    tenant_id: uuid.UUID
    permissions: list[str]


# --- Tenant provisioning (platform admin) ---
class ProvisionTenantRequest(BaseModel):
    slug: str = Field(min_length=1, max_length=63)
    name: str = Field(min_length=1, max_length=255)
    admin_email: EmailStr
    admin_password: str = Field(min_length=12, max_length=200)


class TenantResponse(ORMModel):
    id: uuid.UUID
    slug: str
    name: str
    is_active: bool


# --- Users ---
class CreateUserRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=12, max_length=200)
    full_name: str = Field(default="", max_length=255)


class UserResponse(ORMModel):
    id: uuid.UUID
    email: str
    full_name: str
    is_active: bool


class AssignRoleRequest(BaseModel):
    role_id: uuid.UUID


# --- Roles / permissions ---
class CreateRoleRequest(BaseModel):
    code: str = Field(min_length=1, max_length=64)
    name: str = Field(min_length=1, max_length=128)


class RoleResponse(ORMModel):
    id: uuid.UUID
    code: str
    name: str
    is_system: bool


class PermissionResponse(ORMModel):
    code: str
    description: str


class GrantPermissionRequest(BaseModel):
    permission_code: str = Field(min_length=1, max_length=128)


# --- Org units ---
class CreateOrgUnitRequest(BaseModel):
    code: str = Field(min_length=1, max_length=64)
    name: str = Field(min_length=1, max_length=255)
    unit_type: str = Field(default="department", max_length=64)
    parent_id: uuid.UUID | None = None


class OrgUnitResponse(ORMModel):
    id: uuid.UUID
    code: str
    name: str
    unit_type: str
    parent_id: uuid.UUID | None
    is_active: bool


class PageMeta(BaseModel):
    total: int
    page: int
    size: int
    pages: int

"""Pydantic schemas for request/response validation"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


# Auth schemas
class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: int
    username: str
    created_at: datetime
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True


# Host schemas
class HostCreate(BaseModel):
    hostname: str = Field(..., max_length=100, description="Descriptive name for this host (not used for connection)")
    ip_address: Optional[str] = Field(None, description="Optional IP address for reference")
    gsocket_secret: str = Field(..., description="GSocket secret token - used for connection (both host and panel use same secret)")
    custom_gsrn_server: Optional[str] = Field(None, description="Custom GSRN server (e.g., relay.example.com:443)")
    description: Optional[str] = None
    notes: Optional[str] = None
    tags: Optional[str] = None


class HostUpdate(BaseModel):
    hostname: Optional[str] = Field(None, max_length=100)
    ip_address: Optional[str] = None
    gsocket_secret: Optional[str] = None
    custom_gsrn_server: Optional[str] = Field(None, description="Custom GSRN server (e.g., relay.example.com:443)")
    description: Optional[str] = None
    notes: Optional[str] = None
    tags: Optional[str] = None
    status: Optional[str] = None


class HostResponse(BaseModel):
    id: int
    hostname: str
    ip_address: Optional[str]
    custom_gsrn_server: Optional[str]
    description: Optional[str]
    notes: Optional[str]
    tags: Optional[str]
    status: str
    last_seen: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Script schemas
class ScriptCreate(BaseModel):
    name: str = Field(..., max_length=100)
    description: Optional[str] = None
    content: str
    timeout: int = 300


class ScriptUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    content: Optional[str] = None
    timeout: Optional[int] = None


class ScriptResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    content: str
    timeout: int
    created_by: Optional[int]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Task schemas
class TaskCreate(BaseModel):
    script_id: Optional[int] = None
    script_content: Optional[str] = None  # For ad-hoc scripts
    host_ids: List[int]
    timeout: Optional[int] = 300


class TaskResponse(BaseModel):
    id: int
    script_id: Optional[int]
    host_ids: str
    status: str
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_by: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True


class TaskExecutionResponse(BaseModel):
    id: int
    task_id: int
    host_id: int
    status: str
    exit_code: Optional[int]
    stdout: Optional[str]
    stderr: Optional[str]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    duration_ms: Optional[int]

    class Config:
        from_attributes = True


# Log schemas
class LogResponse(BaseModel):
    id: int
    level: str
    category: Optional[str]
    host_id: Optional[int]
    task_id: Optional[int]
    message: str
    details: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# Stats schemas
class DashboardStats(BaseModel):
    total_hosts: int
    online_hosts: int
    offline_hosts: int
    unknown_hosts: int
    total_tasks: int
    running_tasks: int
    completed_tasks: int
    failed_tasks: int

from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime


# ─── Auth ────────────────────────────────────────────────────────────────────

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class UserOut(BaseModel):
    id: str
    username: str
    email: str
    role: str
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ─── Projects ────────────────────────────────────────────────────────────────

class ProjectCreate(BaseModel):
    title: str
    description: Optional[str] = ""

class ProjectUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None

class MemberOut(BaseModel):
    id: str
    user_id: str
    username: str
    email: str
    role: str
    joined_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class ProjectOut(BaseModel):
    id: str
    title: str
    description: str
    owner_id: str
    owner_name: Optional[str] = None
    created_at: Optional[datetime] = None
    task_count: Optional[int] = 0
    member_count: Optional[int] = 0

    class Config:
        from_attributes = True

class ProjectDetailOut(ProjectOut):
    members: List[MemberOut] = []


# ─── Tasks ───────────────────────────────────────────────────────────────────

class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = ""
    status: str = "To Do"
    priority: str = "Medium"
    project_id: str
    assigned_to: Optional[str] = None
    due_date: Optional[datetime] = None

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    assigned_to: Optional[str] = None
    due_date: Optional[datetime] = None

class TaskOut(BaseModel):
    id: str
    title: str
    description: Optional[str] = ""
    status: str
    priority: str
    due_date: Optional[datetime] = None
    created_at: Optional[datetime] = None
    project_id: str
    assigned_to: Optional[str] = None
    assignee_name: Optional[str] = None

    class Config:
        from_attributes = True


# ─── Members ─────────────────────────────────────────────────────────────────

class AddMember(BaseModel):
    email: str


# ─── Dashboard ───────────────────────────────────────────────────────────────

class DashboardStats(BaseModel):
    total_tasks: int = 0
    todo_count: int = 0
    in_progress_count: int = 0
    done_count: int = 0
    overdue_count: int = 0
    total_projects: int = 0
    recent_tasks: List[TaskOut] = []
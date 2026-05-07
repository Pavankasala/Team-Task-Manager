import os
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from sqlalchemy import or_

import models
import schemas
from database import engine, Base, get_db
from dependencies import get_current_user, get_admin_user
from auth_utils import hash_password, verify_password, create_access_token

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Team Task Manager API")

# CORS — allow local dev + deployed frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ═══════════════════════════════════════════════════════════════════════════════
#  AUTH ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════════

@app.post("/api/signup", response_model=schemas.UserOut)
def signup(user_data: schemas.UserCreate, db: Session = Depends(get_db)):
    """Register a new user."""
    # Check if email or username already taken
    existing = db.query(models.User).filter(
        or_(models.User.email == user_data.email, models.User.username == user_data.username)
    ).first()
    if existing:
        if existing.email == user_data.email:
            raise HTTPException(status_code=400, detail="Email already registered")
        raise HTTPException(status_code=400, detail="Username already taken")

    db_user = models.User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hash_password(user_data.password),
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


@app.post("/api/token", response_model=schemas.Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Login with email (as username field) and password. Returns JWT."""
    user = db.query(models.User).filter(models.User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    token = create_access_token(data={"sub": user.id})
    return {"access_token": token, "token_type": "bearer"}


@app.post("/api/login", response_model=schemas.Token)
def login_json(user_data: schemas.UserLogin, db: Session = Depends(get_db)):
    """Login with JSON body (email + password). Returns JWT."""
    user = db.query(models.User).filter(models.User.email == user_data.email).first()
    if not user or not verify_password(user_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    token = create_access_token(data={"sub": user.id})
    return {"access_token": token, "token_type": "bearer"}


# ═══════════════════════════════════════════════════════════════════════════════
#  USER ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════════

@app.get("/api/users/me", response_model=schemas.UserOut)
def get_me(current_user: models.User = Depends(get_current_user)):
    """Get current authenticated user's profile."""
    return current_user


@app.get("/api/users", response_model=list[schemas.UserOut])
def list_users(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    """List all users (for assignment dropdowns)."""
    return db.query(models.User).all()


# ═══════════════════════════════════════════════════════════════════════════════
#  PROJECT ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════════

@app.post("/api/projects", response_model=schemas.ProjectOut)
def create_project(
    project: schemas.ProjectCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Create a new project. Creator becomes the owner."""
    db_project = models.Project(
        title=project.title,
        description=project.description or "",
        owner_id=current_user.id,
    )
    db.add(db_project)
    db.flush()  # Get the project ID

    # Add creator as owner member
    member = models.ProjectMember(
        project_id=db_project.id,
        user_id=current_user.id,
        role="owner",
    )
    db.add(member)
    db.commit()
    db.refresh(db_project)

    return schemas.ProjectOut(
        id=db_project.id,
        title=db_project.title,
        description=db_project.description,
        owner_id=db_project.owner_id,
        owner_name=current_user.username,
        created_at=db_project.created_at,
        task_count=0,
        member_count=1,
    )


@app.get("/api/projects", response_model=list[schemas.ProjectOut])
def list_projects(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """List projects the current user owns or is a member of."""
    # Get project IDs where user is a member
    member_project_ids = (
        db.query(models.ProjectMember.project_id)
        .filter(models.ProjectMember.user_id == current_user.id)
        .all()
    )
    member_ids_list = [row[0] for row in member_project_ids]
    projects = (
        db.query(models.Project)
        .filter(
            or_(
                models.Project.owner_id == current_user.id,
                models.Project.id.in_(member_ids_list),
            )
        )
        .all()
    )

    result = []
    for p in projects:
        result.append(schemas.ProjectOut(
            id=p.id,
            title=p.title,
            description=p.description,
            owner_id=p.owner_id,
            owner_name=p.owner.username if p.owner else None,
            created_at=p.created_at,
            task_count=len(p.tasks),
            member_count=len(p.members),
        ))
    return result


@app.get("/api/projects/{project_id}", response_model=schemas.ProjectDetailOut)
def get_project(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Get project details with members."""
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    members_out = []
    for m in project.members:
        members_out.append(schemas.MemberOut(
            id=m.id,
            user_id=m.user_id,
            username=m.user.username,
            email=m.user.email,
            role=m.role,
            joined_at=m.joined_at,
        ))

    return schemas.ProjectDetailOut(
        id=project.id,
        title=project.title,
        description=project.description,
        owner_id=project.owner_id,
        owner_name=project.owner.username if project.owner else None,
        created_at=project.created_at,
        task_count=len(project.tasks),
        member_count=len(project.members),
        members=members_out,
    )


@app.put("/api/projects/{project_id}", response_model=schemas.ProjectOut)
def update_project(
    project_id: str,
    updates: schemas.ProjectUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Update a project (owner or admin only)."""
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if project.owner_id != current_user.id and current_user.role != models.UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Not authorized")

    if updates.title is not None:
        project.title = updates.title
    if updates.description is not None:
        project.description = updates.description

    db.commit()
    db.refresh(project)
    return schemas.ProjectOut(
        id=project.id,
        title=project.title,
        description=project.description,
        owner_id=project.owner_id,
        owner_name=project.owner.username if project.owner else None,
        created_at=project.created_at,
        task_count=len(project.tasks),
        member_count=len(project.members),
    )


@app.delete("/api/projects/{project_id}")
def delete_project(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Delete a project (owner or admin only)."""
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if project.owner_id != current_user.id and current_user.role != models.UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Not authorized")

    db.delete(project)
    db.commit()
    return {"message": "Project deleted successfully"}


# ═══════════════════════════════════════════════════════════════════════════════
#  PROJECT MEMBER ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════════

@app.post("/api/projects/{project_id}/members", response_model=schemas.MemberOut)
def add_member(
    project_id: str,
    data: schemas.AddMember,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Add a member to a project by email."""
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if project.owner_id != current_user.id and current_user.role != models.UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Only project owner or admin can add members")

    user = db.query(models.User).filter(models.User.email == data.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found with that email")

    # Check if already a member
    existing = (
        db.query(models.ProjectMember)
        .filter(models.ProjectMember.project_id == project_id, models.ProjectMember.user_id == user.id)
        .first()
    )
    if existing:
        raise HTTPException(status_code=400, detail="User is already a member of this project")

    member = models.ProjectMember(
        project_id=project_id,
        user_id=user.id,
        role="member",
    )
    db.add(member)
    db.commit()
    db.refresh(member)

    return schemas.MemberOut(
        id=member.id,
        user_id=member.user_id,
        username=user.username,
        email=user.email,
        role=member.role,
        joined_at=member.joined_at,
    )


@app.get("/api/projects/{project_id}/members", response_model=list[schemas.MemberOut])
def list_members(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """List all members of a project."""
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    result = []
    for m in project.members:
        result.append(schemas.MemberOut(
            id=m.id,
            user_id=m.user_id,
            username=m.user.username,
            email=m.user.email,
            role=m.role,
            joined_at=m.joined_at,
        ))
    return result


@app.delete("/api/projects/{project_id}/members/{user_id}")
def remove_member(
    project_id: str,
    user_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Remove a member from a project."""
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if project.owner_id != current_user.id and current_user.role != models.UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Not authorized")
    if user_id == project.owner_id:
        raise HTTPException(status_code=400, detail="Cannot remove the project owner")

    member = (
        db.query(models.ProjectMember)
        .filter(models.ProjectMember.project_id == project_id, models.ProjectMember.user_id == user_id)
        .first()
    )
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    db.delete(member)
    db.commit()
    return {"message": "Member removed"}


# ═══════════════════════════════════════════════════════════════════════════════
#  TASK ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════════

@app.post("/api/tasks", response_model=schemas.TaskOut)
def create_task(
    task: schemas.TaskCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Create a new task within a project."""
    # Verify project exists
    project = db.query(models.Project).filter(models.Project.id == task.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    db_task = models.Task(
        title=task.title,
        description=task.description or "",
        status=task.status,
        priority=task.priority,
        project_id=task.project_id,
        assigned_to=task.assigned_to,
        due_date=task.due_date,
    )
    db.add(db_task)
    db.commit()
    db.refresh(db_task)

    assignee_name = None
    if db_task.assignee:
        assignee_name = db_task.assignee.username

    return schemas.TaskOut(
        id=db_task.id,
        title=db_task.title,
        description=db_task.description,
        status=db_task.status,
        priority=db_task.priority,
        due_date=db_task.due_date,
        created_at=db_task.created_at,
        project_id=db_task.project_id,
        assigned_to=db_task.assigned_to,
        assignee_name=assignee_name,
    )


@app.get("/api/projects/{project_id}/tasks", response_model=list[schemas.TaskOut])
def get_project_tasks(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """List all tasks for a project."""
    tasks = db.query(models.Task).filter(models.Task.project_id == project_id).all()
    result = []
    for t in tasks:
        result.append(schemas.TaskOut(
            id=t.id,
            title=t.title,
            description=t.description,
            status=t.status,
            priority=t.priority,
            due_date=t.due_date,
            created_at=t.created_at,
            project_id=t.project_id,
            assigned_to=t.assigned_to,
            assignee_name=t.assignee.username if t.assignee else None,
        ))
    return result


@app.put("/api/tasks/{task_id}", response_model=schemas.TaskOut)
def update_task(
    task_id: str,
    updates: schemas.TaskUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Update a task (status, assignee, due date, etc.)."""
    task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if updates.title is not None:
        task.title = updates.title
    if updates.description is not None:
        task.description = updates.description
    if updates.status is not None:
        task.status = updates.status
    if updates.priority is not None:
        task.priority = updates.priority
    if updates.assigned_to is not None:
        task.assigned_to = updates.assigned_to if updates.assigned_to else None
    if updates.due_date is not None:
        task.due_date = updates.due_date

    db.commit()
    db.refresh(task)

    return schemas.TaskOut(
        id=task.id,
        title=task.title,
        description=task.description,
        status=task.status,
        priority=task.priority,
        due_date=task.due_date,
        created_at=task.created_at,
        project_id=task.project_id,
        assigned_to=task.assigned_to,
        assignee_name=task.assignee.username if task.assignee else None,
    )


@app.delete("/api/tasks/{task_id}")
def delete_task(
    task_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Delete a task."""
    task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    db.delete(task)
    db.commit()
    return {"message": "Task deleted successfully"}


# ═══════════════════════════════════════════════════════════════════════════════
#  DASHBOARD ENDPOINT
# ═══════════════════════════════════════════════════════════════════════════════

@app.get("/api/dashboard", response_model=schemas.DashboardStats)
def get_dashboard(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Get dashboard statistics for the current user."""
    # Get all project IDs the user is involved in
    member_project_ids = [
        m.project_id for m in
        db.query(models.ProjectMember)
        .filter(models.ProjectMember.user_id == current_user.id)
        .all()
    ]
    owned_project_ids = [
        p.id for p in
        db.query(models.Project)
        .filter(models.Project.owner_id == current_user.id)
        .all()
    ]
    all_project_ids = list(set(member_project_ids + owned_project_ids))

    # Get all tasks across user's projects
    tasks = db.query(models.Task).filter(models.Task.project_id.in_(all_project_ids)).all()

    now = datetime.now(timezone.utc)
    todo = sum(1 for t in tasks if t.status == "To Do")
    in_progress = sum(1 for t in tasks if t.status == "In Progress")
    done = sum(1 for t in tasks if t.status == "Done")
    overdue = sum(
        1 for t in tasks
        if t.due_date and t.due_date.replace(tzinfo=timezone.utc) < now and t.status != "Done"
    )

    # Recent tasks (last 10)
    recent = sorted(tasks, key=lambda t: t.created_at or now, reverse=True)[:10]
    recent_out = []
    for t in recent:
        recent_out.append(schemas.TaskOut(
            id=t.id,
            title=t.title,
            description=t.description,
            status=t.status,
            priority=t.priority,
            due_date=t.due_date,
            created_at=t.created_at,
            project_id=t.project_id,
            assigned_to=t.assigned_to,
            assignee_name=t.assignee.username if t.assignee else None,
        ))

    return schemas.DashboardStats(
        total_tasks=len(tasks),
        todo_count=todo,
        in_progress_count=in_progress,
        done_count=done,
        overdue_count=overdue,
        total_projects=len(all_project_ids),
        recent_tasks=recent_out,
    )


# ═══════════════════════════════════════════════════════════════════════════════
#  SERVE REACT FRONTEND (production)
# ═══════════════════════════════════════════════════════════════════════════════

# Serve the built React app
# In Docker: files are in /app/static
# In local dev: files are in ../frontend/dist
static_path = Path(__file__).parent / "static"
if not static_path.exists():
    static_path = Path(__file__).parent.parent / "frontend" / "dist"
if static_path.exists():
    app.mount("/", StaticFiles(directory=str(static_path), html=True), name="frontend")


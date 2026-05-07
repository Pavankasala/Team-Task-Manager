# Team Task Manager

A full-stack web application for managing projects, assigning tasks, and tracking progress with role-based access control.

## 🚀 Features

- **Authentication** — Signup/Login with JWT tokens
- **Role-Based Access Control** — Admin and Member roles with permission-based actions
- **Project Management** — Create, update, and delete projects
- **Team Management** — Add/remove team members to projects by email
- **Task Management** — Create tasks with title, description, priority, assignee, and due date
- **Kanban Board** — Visual task board with To Do / In Progress / Done columns
- **Status Tracking** — Change task status with a dropdown
- **Dashboard** — Overview with stats (total tasks, overdue, by status) and recent tasks
- **Overdue Detection** — Visual indicators for tasks past their due date
- **UUID Primary Keys** — All entities use UUID identifiers

## ⚙️ Tech Stack

### Backend
- **Framework:** FastAPI (Python)
- **Database:** PostgreSQL (production) / SQLite (development)
- **ORM:** SQLAlchemy
- **Auth:** JWT (python-jose) + bcrypt password hashing
- **Validation:** Pydantic

### Frontend
- **Framework:** React 19 (Vite)
- **Routing:** React Router v7
- **HTTP Client:** Axios with JWT interceptors
- **Styling:** Custom CSS with dark theme, glassmorphism, and micro-animations

## 📂 Project Structure

```
Team Task Manager/
├── backend/
│   ├── main.py              # FastAPI app + all API routes
│   ├── models.py            # SQLAlchemy models (User, Project, Task, ProjectMember)
│   ├── schemas.py           # Pydantic request/response schemas
│   ├── database.py          # Database engine configuration
│   ├── auth_utils.py        # Password hashing + JWT creation
│   ├── dependencies.py      # Auth dependency injection
│   └── requirements.txt     # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── context/         # AuthContext for global auth state
│   │   ├── pages/           # Login, Signup, Dashboard, Projects, ProjectDetail
│   │   ├── components/      # Navbar, TaskCard, StatsCard, ProtectedRoute
│   │   └── services/        # Axios API client
│   └── package.json
├── Procfile                  # Railway process file
├── railway.toml              # Railway build configuration
└── README.md
```

## 🔌 API Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/api/signup` | ❌ | Register new user |
| POST | `/api/login` | ❌ | Login (JSON body) |
| POST | `/api/token` | ❌ | Login (OAuth2 form) |
| GET | `/api/users/me` | ✅ | Get current user |
| GET | `/api/users` | ✅ | List all users |
| POST | `/api/projects` | ✅ | Create project |
| GET | `/api/projects` | ✅ | List user's projects |
| GET | `/api/projects/:id` | ✅ | Get project detail |
| PUT | `/api/projects/:id` | ✅ | Update project (owner/admin) |
| DELETE | `/api/projects/:id` | ✅ | Delete project (owner/admin) |
| POST | `/api/projects/:id/members` | ✅ | Add member by email |
| GET | `/api/projects/:id/members` | ✅ | List members |
| DELETE | `/api/projects/:id/members/:uid` | ✅ | Remove member |
| POST | `/api/tasks` | ✅ | Create task |
| GET | `/api/projects/:id/tasks` | ✅ | List project tasks |
| PUT | `/api/tasks/:id` | ✅ | Update task |
| DELETE | `/api/tasks/:id` | ✅ | Delete task |
| GET | `/api/dashboard` | ✅ | Dashboard statistics |

## 🛠️ Local Development

### Prerequisites
- Python 3.10+
- Node.js 18+

### Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

The Vite dev server proxies `/api` requests to `http://localhost:8000`.

## 🌐 Deployment (Railway)

1. Push code to GitHub
2. Create a new project on [Railway](https://railway.app)
3. Add a **PostgreSQL** database service
4. Connect your GitHub repo
5. Set environment variables:
   - `DATABASE_URL` — auto-set by Railway PostgreSQL addon
   - `SECRET_KEY` — a random secret string for JWT signing
6. Deploy — Railway uses `railway.toml` for build/start commands

## 📝 Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | SQLite (local) |
| `SECRET_KEY` | JWT signing secret | `dev-secret-key...` |

## 👤 Roles

- **Admin** — Can manage all projects, add/remove members, delete any project
- **Member** — Can create projects, manage own projects, create/update tasks

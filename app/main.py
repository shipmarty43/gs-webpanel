"""Main application entry point"""
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from app.config import settings
from app.database import Base, engine
from app.routes import auth, hosts, scripts, tasks, logs, reports, terminal

# Create database tables
Base.metadata.create_all(bind=engine)

# Create FastAPI app
app = FastAPI(
    title="GSocket C2 Panel",
    description="Web panel for centralized management of workstations via gsocket",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates
templates = Jinja2Templates(directory="app/templates")

# Include routers
app.include_router(auth.router)
app.include_router(hosts.router)
app.include_router(scripts.router)
app.include_router(tasks.router)
app.include_router(logs.router)
app.include_router(reports.router)
app.include_router(terminal.router)


# Health check
@app.get("/api/health")
def health_check():
    """Health check endpoint"""
    return {
        "status": "ok",
        "version": "1.0.0"
    }


# Frontend routes
@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    """Dashboard page"""
    return templates.TemplateResponse("dashboard.html", {"request": request})


@app.get("/hosts", response_class=HTMLResponse)
def hosts_page(request: Request):
    """Hosts management page"""
    return templates.TemplateResponse("hosts.html", {"request": request})


@app.get("/scripts", response_class=HTMLResponse)
def scripts_page(request: Request):
    """Scripts management page"""
    return templates.TemplateResponse("scripts.html", {"request": request})


@app.get("/tasks", response_class=HTMLResponse)
def tasks_page(request: Request):
    """Tasks management page"""
    return templates.TemplateResponse("tasks.html", {"request": request})


@app.get("/logs", response_class=HTMLResponse)
def logs_page(request: Request):
    """Logs page"""
    return templates.TemplateResponse("logs.html", {"request": request})


@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    """Login page"""
    return templates.TemplateResponse("login.html", {"request": request})


@app.get("/terminal/{host_id}", response_class=HTMLResponse)
def terminal_page(request: Request, host_id: int):
    """Web terminal page"""
    return templates.TemplateResponse("terminal.html", {"request": request, "host_id": host_id})


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )

"""Reporting and dashboard routes"""
from typing import List
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app.models.host import Host
from app.models.task import Task, TaskExecution
from app.models.log import PingHistory
from app.models.user import User
from app.schemas import DashboardStats
from app.utils.auth import get_current_user
import csv
import io

router = APIRouter(prefix="/api/reports", tags=["reports"])


@router.get("/dashboard", response_model=DashboardStats)
def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get dashboard statistics"""

    # Host stats
    total_hosts = db.query(Host).count()
    online_hosts = db.query(Host).filter(Host.status == "online").count()
    offline_hosts = db.query(Host).filter(Host.status == "offline").count()
    unknown_hosts = db.query(Host).filter(Host.status == "unknown").count()

    # Task stats
    total_tasks = db.query(Task).count()
    running_tasks = db.query(Task).filter(Task.status == "running").count()
    completed_tasks = db.query(Task).filter(Task.status == "completed").count()
    failed_tasks = db.query(Task).filter(Task.status == "failed").count()

    return DashboardStats(
        total_hosts=total_hosts,
        online_hosts=online_hosts,
        offline_hosts=offline_hosts,
        unknown_hosts=unknown_hosts,
        total_tasks=total_tasks,
        running_tasks=running_tasks,
        completed_tasks=completed_tasks,
        failed_tasks=failed_tasks
    )


@router.get("/host/{host_id}")
def get_host_report(
    host_id: int,
    days: int = Query(7, description="Number of days for history"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get detailed report for a specific host"""

    host = db.query(Host).filter(Host.id == host_id).first()
    if not host:
        return {"error": "Host not found"}

    # Get ping history
    cutoff = datetime.utcnow() - timedelta(days=days)
    ping_history = db.query(PingHistory).filter(
        PingHistory.host_id == host_id,
        PingHistory.checked_at >= cutoff
    ).order_by(PingHistory.checked_at.desc()).limit(1000).all()

    # Get task executions
    task_executions = db.query(TaskExecution).filter(
        TaskExecution.host_id == host_id
    ).order_by(TaskExecution.created_at.desc()).limit(100).all()

    # Calculate uptime percentage
    total_pings = len(ping_history)
    online_pings = sum(1 for p in ping_history if p.status == "online")
    uptime_percentage = (online_pings / total_pings * 100) if total_pings > 0 else 0

    # Task success rate
    total_executions = len(task_executions)
    successful_executions = sum(1 for e in task_executions if e.status == "success")
    success_rate = (successful_executions / total_executions * 100) if total_executions > 0 else 0

    return {
        "host": {
            "id": host.id,
            "hostname": host.hostname,
            "ip_address": host.ip_address,
            "status": host.status,
            "last_seen": host.last_seen
        },
        "uptime_percentage": round(uptime_percentage, 2),
        "success_rate": round(success_rate, 2),
        "total_tasks": total_executions,
        "ping_history": [
            {
                "status": p.status,
                "response_time_ms": p.response_time_ms,
                "checked_at": p.checked_at
            }
            for p in ping_history[:100]
        ],
        "recent_executions": [
            {
                "task_id": e.task_id,
                "status": e.status,
                "exit_code": e.exit_code,
                "duration_ms": e.duration_ms,
                "completed_at": e.completed_at
            }
            for e in task_executions[:20]
        ]
    }


@router.get("/task/{task_id}")
def get_task_report(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get detailed report for a specific task"""

    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        return {"error": "Task not found"}

    # Get all executions
    executions = db.query(TaskExecution).filter(
        TaskExecution.task_id == task_id
    ).all()

    # Calculate stats
    stats = {
        "total": len(executions),
        "success": sum(1 for e in executions if e.status == "success"),
        "failed": sum(1 for e in executions if e.status == "failed"),
        "timeout": sum(1 for e in executions if e.status == "timeout"),
        "pending": sum(1 for e in executions if e.status == "pending"),
        "running": sum(1 for e in executions if e.status == "running")
    }

    # Average duration
    completed = [e for e in executions if e.duration_ms is not None]
    avg_duration = sum(e.duration_ms for e in completed) / len(completed) if completed else 0

    return {
        "task": {
            "id": task.id,
            "status": task.status,
            "started_at": task.started_at,
            "completed_at": task.completed_at
        },
        "statistics": stats,
        "average_duration_ms": round(avg_duration, 2),
        "executions": [
            {
                "id": e.id,
                "host_id": e.host_id,
                "status": e.status,
                "exit_code": e.exit_code,
                "duration_ms": e.duration_ms,
                "started_at": e.started_at,
                "completed_at": e.completed_at
            }
            for e in executions
        ]
    }


@router.get("/export")
def export_task_results(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Export task results to CSV"""

    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        return {"error": "Task not found"}

    executions = db.query(TaskExecution, Host).join(
        Host, TaskExecution.host_id == Host.id
    ).filter(TaskExecution.task_id == task_id).all()

    # Create CSV
    output = io.StringIO()
    writer = csv.writer(output)

    # Header
    writer.writerow(['host_id', 'hostname', 'status', 'exit_code', 'duration_ms', 'started_at', 'completed_at', 'stdout_preview', 'stderr_preview'])

    # Data
    for execution, host in executions:
        stdout_preview = (execution.stdout[:100] + '...') if execution.stdout and len(execution.stdout) > 100 else (execution.stdout or '')
        stderr_preview = (execution.stderr[:100] + '...') if execution.stderr and len(execution.stderr) > 100 else (execution.stderr or '')

        writer.writerow([
            host.id,
            host.hostname,
            execution.status,
            execution.exit_code or '',
            execution.duration_ms or '',
            execution.started_at.isoformat() if execution.started_at else '',
            execution.completed_at.isoformat() if execution.completed_at else '',
            stdout_preview,
            stderr_preview
        ])

    output.seek(0)

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=task_{task_id}_results.csv"}
    )


@router.get("/availability")
def get_availability_history(
    hours: int = Query(24, description="Hours of history"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get host availability history for charts"""

    cutoff = datetime.utcnow() - timedelta(hours=hours)

    # Get ping history grouped by hour
    results = db.query(
        func.strftime('%Y-%m-%d %H:00:00', PingHistory.checked_at).label('hour'),
        func.sum(func.case((PingHistory.status == 'online', 1), else_=0)).label('online'),
        func.count(PingHistory.id).label('total')
    ).filter(
        PingHistory.checked_at >= cutoff
    ).group_by('hour').order_by('hour').all()

    return {
        "data": [
            {
                "timestamp": r.hour,
                "online_count": r.online,
                "total_checks": r.total,
                "online_percentage": round((r.online / r.total * 100) if r.total > 0 else 0, 2)
            }
            for r in results
        ]
    }

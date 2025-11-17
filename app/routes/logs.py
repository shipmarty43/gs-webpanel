"""Logging and monitoring routes"""
from typing import List, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.database import get_db
from app.models.log import Log
from app.models.user import User
from app.schemas import LogResponse
from app.utils.auth import get_current_user
import csv
import io

router = APIRouter(prefix="/api/logs", tags=["logs"])


@router.get("", response_model=List[LogResponse])
def get_logs(
    level: Optional[str] = Query(None, description="Filter by log level"),
    category: Optional[str] = Query(None, description="Filter by category"),
    host_id: Optional[int] = Query(None, description="Filter by host ID"),
    task_id: Optional[int] = Query(None, description="Filter by task ID"),
    hours: Optional[int] = Query(24, description="Last N hours"),
    limit: int = Query(100, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get logs with filtering"""

    # Build query
    query = db.query(Log)

    # Time filter
    if hours:
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        query = query.filter(Log.created_at >= cutoff)

    # Level filter
    if level:
        query = query.filter(Log.level == level.upper())

    # Category filter
    if category:
        query = query.filter(Log.category == category)

    # Host filter
    if host_id:
        query = query.filter(Log.host_id == host_id)

    # Task filter
    if task_id:
        query = query.filter(Log.task_id == task_id)

    # Order and limit
    logs = query.order_by(Log.created_at.desc()).limit(limit).all()

    return logs


@router.get("/export")
def export_logs(
    level: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    host_id: Optional[int] = Query(None),
    hours: Optional[int] = Query(24),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Export logs to CSV"""

    # Build query
    query = db.query(Log)

    # Time filter
    if hours:
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        query = query.filter(Log.created_at >= cutoff)

    # Apply filters
    if level:
        query = query.filter(Log.level == level.upper())
    if category:
        query = query.filter(Log.category == category)
    if host_id:
        query = query.filter(Log.host_id == host_id)

    logs = query.order_by(Log.created_at.desc()).limit(10000).all()

    # Create CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)

    # Header
    writer.writerow(['timestamp', 'level', 'category', 'host_id', 'task_id', 'message', 'details'])

    # Data
    for log in logs:
        writer.writerow([
            log.created_at.isoformat(),
            log.level,
            log.category or '',
            log.host_id or '',
            log.task_id or '',
            log.message,
            log.details or ''
        ])

    output.seek(0)

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"}
    )

"""Task management and execution routes"""
import json
import asyncio
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.task import Task, TaskExecution
from app.models.host import Host
from app.models.user import User
from app.schemas import TaskCreate, TaskResponse, TaskExecutionResponse
from app.utils.auth import get_current_user
from app.services.task_executor import task_executor
from app.services.logger_service import logger_service

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


def run_task_async(db: Session, task_id: int):
    """Run task execution in background"""
    asyncio.run(task_executor.execute_task(db, task_id))


@router.get("", response_model=List[TaskResponse])
def list_tasks(
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List recent tasks"""

    tasks = db.query(Task).order_by(Task.created_at.desc()).limit(limit).all()
    return tasks


@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
def create_task(
    task_data: TaskCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create and execute a new task"""

    # Validate host IDs
    if not task_data.host_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one host must be specified"
        )

    # Check hosts exist
    hosts = db.query(Host).filter(Host.id.in_(task_data.host_ids)).all()
    if len(hosts) != len(task_data.host_ids):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="One or more host IDs are invalid"
        )

    # Create task
    task = Task(
        script_id=task_data.script_id,
        host_ids=json.dumps(task_data.host_ids),
        status="pending",
        created_by=current_user.id
    )

    db.add(task)
    db.commit()
    db.refresh(task)

    logger_service.info(
        db,
        f"Task created with {len(task_data.host_ids)} hosts",
        category="execution",
        task_id=task.id
    )

    # Execute task in background
    background_tasks.add_task(run_task_async, db, task.id)

    return task


@router.get("/{task_id}", response_model=TaskResponse)
def get_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get task details"""

    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    return task


@router.get("/{task_id}/status")
def get_task_status(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get task execution status"""

    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    # Get execution stats
    executions = db.query(TaskExecution).filter(TaskExecution.task_id == task_id).all()

    stats = {
        "task_id": task.id,
        "status": task.status,
        "total_hosts": len(executions),
        "pending": sum(1 for e in executions if e.status == "pending"),
        "running": sum(1 for e in executions if e.status == "running"),
        "success": sum(1 for e in executions if e.status == "success"),
        "failed": sum(1 for e in executions if e.status == "failed"),
        "timeout": sum(1 for e in executions if e.status == "timeout"),
        "started_at": task.started_at,
        "completed_at": task.completed_at
    }

    return stats


@router.get("/{task_id}/results", response_model=List[TaskExecutionResponse])
def get_task_results(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get detailed task execution results"""

    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    executions = db.query(TaskExecution).filter(
        TaskExecution.task_id == task_id
    ).all()

    return executions


@router.post("/{task_id}/retry")
def retry_failed_executions(
    task_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retry failed task executions"""

    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    # Get failed executions
    failed_executions = db.query(TaskExecution).filter(
        TaskExecution.task_id == task_id,
        TaskExecution.status.in_(["failed", "timeout"])
    ).all()

    if not failed_executions:
        return {"message": "No failed executions to retry"}

    # Get failed host IDs
    failed_host_ids = [e.host_id for e in failed_executions]

    # Create new task for retry
    retry_task = Task(
        script_id=task.script_id,
        host_ids=json.dumps(failed_host_ids),
        status="pending",
        created_by=current_user.id
    )

    db.add(retry_task)
    db.commit()
    db.refresh(retry_task)

    logger_service.info(
        db,
        f"Retry task created for {len(failed_host_ids)} failed hosts",
        category="execution",
        task_id=retry_task.id
    )

    # Execute retry task in background
    background_tasks.add_task(run_task_async, db, retry_task.id)

    return {
        "message": f"Retry task created for {len(failed_host_ids)} hosts",
        "retry_task_id": retry_task.id
    }


@router.post("/quick-execute")
async def quick_execute_command(
    request_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Quickly execute a command on a host and return result

    This is used for quick actions like getting hostname, checking connectivity, etc.
    Does not create a task in the database.

    Request body:
    {
        "host_id": 1,
        "command": "hostname",
        "timeout": 10
    }
    """
    from app.services.gsocket_service import gsocket_service

    host_id = request_data.get("host_id")
    command = request_data.get("command")
    timeout = request_data.get("timeout", 10)

    if not host_id or not command:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="host_id and command are required"
        )

    # Get host
    host = db.query(Host).filter(Host.id == host_id).first()
    if not host:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Host not found"
        )

    try:
        # Execute command
        result = await gsocket_service.execute_command(
            secret=host.gsocket_secret,
            command=command,
            timeout=timeout,
            custom_gsrn_server=host.custom_gsrn_server
        )

        logger_service.info(
            db,
            f"Quick execute on {host.hostname}: {command}",
            category="execution",
            host_id=host.id
        )

        return {
            "success": result["success"],
            "output": result.get("stdout", ""),
            "error": result.get("stderr", ""),
            "exit_code": result.get("exit_code"),
            "message": result.get("message", "")
        }

    except Exception as e:
        logger_service.error(
            db,
            f"Quick execute failed on {host.hostname}: {str(e)}",
            category="execution",
            host_id=host.id
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Command execution failed: {str(e)}"
        )

"""Task executor service for parallel task execution"""
import asyncio
from datetime import datetime
from typing import List
from sqlalchemy.orm import Session
from app.models.task import Task, TaskExecution
from app.models.host import Host
from app.models.script import Script
from app.services.gsocket_service import gsocket_service
from app.services.logger_service import logger_service
from app.config import settings
import logging

logger = logging.getLogger(__name__)


class TaskExecutorService:
    """Service for executing tasks on multiple hosts in parallel"""

    @staticmethod
    async def execute_task(db: Session, task_id: int):
        """
        Execute a task on all specified hosts

        Args:
            db: Database session
            task_id: Task ID to execute
        """
        # Get task
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            logger.error(f"Task {task_id} not found")
            return

        # Update task status
        task.status = "running"
        task.started_at = datetime.utcnow()
        db.commit()

        logger_service.info(
            db,
            f"Starting task execution",
            category="execution",
            task_id=task.id
        )

        # Get script content
        if task.script_id:
            script = db.query(Script).filter(Script.id == task.script_id).first()
            if not script:
                task.status = "failed"
                task.completed_at = datetime.utcnow()
                db.commit()
                logger_service.error(
                    db,
                    f"Script {task.script_id} not found",
                    category="execution",
                    task_id=task.id
                )
                return
            script_content = script.content
            script_timeout = script.timeout
        else:
            # Ad-hoc script (stored in host_ids as JSON)
            script_content = "echo 'No script provided'"
            script_timeout = settings.DEFAULT_TASK_TIMEOUT

        # Parse host IDs
        import json
        try:
            host_ids = json.loads(task.host_ids)
        except:
            host_ids = []

        # Get hosts
        hosts = db.query(Host).filter(Host.id.in_(host_ids)).all()

        # Create task executions
        executions = []
        for host in hosts:
            execution = TaskExecution(
                task_id=task.id,
                host_id=host.id,
                status="pending"
            )
            db.add(execution)
            executions.append(execution)

        db.commit()

        # Execute on all hosts in parallel (with concurrency limit)
        semaphore = asyncio.Semaphore(settings.MAX_CONCURRENT_TASKS)

        async def execute_on_host(execution: TaskExecution, host: Host):
            async with semaphore:
                await TaskExecutorService._execute_on_single_host(
                    db, execution, host, script_content, script_timeout
                )

        # Run all executions
        tasks_list = [execute_on_host(exec, host) for exec, host in zip(executions, hosts)]
        await asyncio.gather(*tasks_list, return_exceptions=True)

        # Update task status
        db.refresh(task)
        executions = db.query(TaskExecution).filter(TaskExecution.task_id == task.id).all()

        success_count = sum(1 for e in executions if e.status == "success")
        failed_count = sum(1 for e in executions if e.status in ["failed", "timeout"])

        if failed_count == 0:
            task.status = "completed"
        elif success_count > 0:
            task.status = "completed"  # Partial success
        else:
            task.status = "failed"

        task.completed_at = datetime.utcnow()
        db.commit()

        logger_service.info(
            db,
            f"Task completed: {success_count} succeeded, {failed_count} failed",
            category="execution",
            task_id=task.id
        )

    @staticmethod
    async def _execute_on_single_host(
        db: Session,
        execution: TaskExecution,
        host: Host,
        script_content: str,
        timeout: int
    ):
        """Execute script on a single host"""

        # Update execution status
        execution.status = "running"
        execution.started_at = datetime.utcnow()
        db.commit()

        logger_service.info(
            db,
            f"Executing on host {host.hostname}",
            category="execution",
            host_id=host.id,
            task_id=execution.task_id
        )

        # Execute via gsocket
        result = await gsocket_service.execute_command(
            secret=host.gsocket_secret,
            command=script_content,
            timeout=timeout
        )

        # Update execution with results
        execution.exit_code = result["exit_code"]
        execution.stdout = result["stdout"]
        execution.stderr = result["stderr"]
        execution.duration_ms = result["duration_ms"]
        execution.completed_at = datetime.utcnow()

        if result["exit_code"] == 0:
            execution.status = "success"
        elif "timed out" in result["stderr"]:
            execution.status = "timeout"
        else:
            execution.status = "failed"

        db.commit()

        logger_service.info(
            db,
            f"Execution on {host.hostname} {execution.status}: exit_code={result['exit_code']}",
            category="execution",
            host_id=host.id,
            task_id=execution.task_id
        )


# Singleton instance
task_executor = TaskExecutorService()

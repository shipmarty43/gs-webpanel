"""Task and TaskExecution models"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Index
from sqlalchemy.sql import func
from app.database import Base


class Task(Base):
    """Task model for script execution tasks"""

    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    script_id = Column(Integer, ForeignKey("scripts.id"), nullable=True)
    host_ids = Column(Text, nullable=False)  # JSON array of host IDs
    status = Column(String(20), default="pending")  # pending/running/completed/failed
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<Task(id={self.id}, status='{self.status}')>"


class TaskExecution(Base):
    """TaskExecution model for individual host execution results"""

    __tablename__ = "task_executions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    host_id = Column(Integer, ForeignKey("hosts.id"), nullable=False)
    status = Column(String(20), default="pending")  # pending/running/success/failed/timeout
    exit_code = Column(Integer, nullable=True)
    stdout = Column(Text, nullable=True)
    stderr = Column(Text, nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    duration_ms = Column(Integer, nullable=True)

    def __repr__(self):
        return f"<TaskExecution(id={self.id}, task_id={self.task_id}, host_id={self.host_id}, status='{self.status}')>"


# Create indexes
Index('idx_tasks_status', Task.status)
Index('idx_tasks_created_at', Task.created_at)
Index('idx_task_exec_task_id', TaskExecution.task_id)
Index('idx_task_exec_host_id', TaskExecution.host_id)
Index('idx_task_exec_status', TaskExecution.status)

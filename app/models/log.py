"""Log model"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Index
from sqlalchemy.sql import func
from app.database import Base


class Log(Base):
    """Log model for system logging"""

    __tablename__ = "logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    level = Column(String(20), nullable=False)  # INFO/WARNING/ERROR/DEBUG
    category = Column(String(50), nullable=True)  # connection/execution/system/auth
    host_id = Column(Integer, ForeignKey("hosts.id"), nullable=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=True)
    message = Column(Text, nullable=False)
    details = Column(Text, nullable=True)  # JSON for additional data
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    def __repr__(self):
        return f"<Log(id={self.id}, level='{self.level}', category='{self.category}')>"


class PingHistory(Base):
    """PingHistory model for host availability tracking"""

    __tablename__ = "ping_history"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    host_id = Column(Integer, ForeignKey("hosts.id"), nullable=False)
    status = Column(String(20), nullable=False)  # online/offline
    response_time_ms = Column(Integer, nullable=True)
    checked_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<PingHistory(id={self.id}, host_id={self.host_id}, status='{self.status}')>"


# Create indexes
Index('idx_logs_created_at', Log.created_at)
Index('idx_logs_level', Log.level)
Index('idx_logs_category', Log.category)
Index('idx_logs_host_id', Log.host_id)
Index('idx_ping_host_id', PingHistory.host_id)
Index('idx_ping_checked_at', PingHistory.checked_at)

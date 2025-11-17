"""Host model"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Index
from sqlalchemy.sql import func
from app.database import Base


class Host(Base):
    """Host model for managed workstations"""

    __tablename__ = "hosts"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    hostname = Column(String(100), nullable=False, index=True)
    ip_address = Column(String(45), nullable=True)
    gsocket_secret = Column(String(255), nullable=False)  # encrypted
    description = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)  # User notes/comments
    tags = Column(Text, nullable=True)  # JSON array as string
    status = Column(String(20), default="unknown")  # online/offline/unknown
    last_seen = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<Host(id={self.id}, hostname='{self.hostname}', status='{self.status}')>"


# Create indexes
Index('idx_hosts_status', Host.status)
Index('idx_hosts_last_seen', Host.last_seen)

"""Application settings model"""
from sqlalchemy import Column, Integer, String, Boolean, Text
from app.database import Base


class Settings(Base):
    """Application runtime settings"""
    __tablename__ = "settings"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(100), unique=True, nullable=False, index=True)
    value = Column(Text, nullable=False)
    value_type = Column(String(20), nullable=False)  # int, str, bool, float
    category = Column(String(50), nullable=False)  # monitoring, security, tasks, etc.
    description = Column(Text)

    def get_typed_value(self):
        """Convert string value to proper type"""
        if self.value_type == "int":
            return int(self.value)
        elif self.value_type == "float":
            return float(self.value)
        elif self.value_type == "bool":
            return self.value.lower() in ('true', '1', 'yes')
        else:
            return self.value

    def set_typed_value(self, val):
        """Set value with type conversion"""
        self.value = str(val)

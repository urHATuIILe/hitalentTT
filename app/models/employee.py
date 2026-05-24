from sqlalchemy import Column, Integer, String, Date, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import TimestampMixin
from app.database import Base


class Employee(TimestampMixin, Base):
    __tablename__ = "employees"

    id = Column(Integer, primary_key=True, index=True)
    department_id = Column(
        Integer,
        ForeignKey("departments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    full_name = Column(String(200), nullable=False)
    position = Column(String(200), nullable=False)
    hired_at = Column(Date, nullable=True)

    department = relationship("Department", back_populates="employees")

    def __repr__(self):
        return f"<Employee(id={self.id}, name='{self.full_name}', pos='{self.position}')>"

from sqlalchemy import Column, Integer, String, ForeignKey, UniqueConstraint, Index
from sqlalchemy.orm import relationship
from app.models.base import TimestampMixin
from app.database import Base


class Department(TimestampMixin, Base):
    __tablename__ = "departments"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    parent_id = Column(
        Integer,
        ForeignKey("departments.id", ondelete="CASCADE"),
        nullable=True,
    )

    parent = relationship("Department", remote_side=[id], back_populates="children")
    children = relationship("Department", back_populates="parent", order_by="Department.name")
    employees = relationship(
        "Employee",
        back_populates="department",
        cascade="all, delete-orphan",
        order_by="Employee.created_at",
    )

    __table_args__ = (
        UniqueConstraint("name", "parent_id", name="uq_department_name_parent"),
        Index("ix_departments_parent_id", "parent_id"),
    )

    def __repr__(self):
        return f"<Department(id={self.id}, name='{self.name}', parent_id={self.parent_id})>"

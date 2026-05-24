from datetime import datetime, timezone
from sqlalchemy import Column, DateTime
from sqlalchemy.orm import declared_attr


class TimestampMixin:
    @declared_attr
    def created_at(cls):
        return Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

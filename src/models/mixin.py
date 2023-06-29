from sqlalchemy import Column, DateTime
from datetime import datetime

from sqlalchemy.orm import declarative_mixin


@declarative_mixin
class TimestampMixin(object):
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.now, onupdate=datetime.now, nullable=False
    )

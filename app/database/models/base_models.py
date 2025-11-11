from sqlalchemy.orm import DeclarativeBase, declared_attr
from sqlalchemy import Column, DateTime, func

class TimestampMixin:
    @declared_attr
    def created_at(cls):
        return Column(DateTime, default=func.now())
    
    @declared_attr
    def updated_at(cls):
        return Column(DateTime, default=func.now(), onupdate=func.now())


class Base(DeclarativeBase, TimestampMixin):
    pass



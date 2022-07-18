from datetime import datetime
from sqlalchemy import ARRAY, Column, Enum, ForeignKey, Integer, String, DateTime
from sqlalchemy.orm import relationship
from dataAdapter.database import Base


class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    email = Column(String(255), nullable=False)
    password = Column(String(255), nullable=False)
    role = Column(String(255))
    subscriptions = Column(ARRAY(Integer))
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    user_courses = relationship('UserCourse', back_populates='user')
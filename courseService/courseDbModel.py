from dataAdapter.database import Base
from datetime import datetime
from sqlalchemy import ARRAY, Column, Integer, String, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship

class UserCourse(Base):
    __tablename__ = 'user_courses'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    course_name = Column(String, nullable=False)
    table_name = Column(String, nullable=False)
    course_details = Column(JSON)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    course_link=Column(String)
    subscribers = Column(ARRAY(Integer))

    user = relationship('User', back_populates='user_courses')

    

class Utility(Base):
    __tablename__ = 'utility'
    id = Column(Integer, primary_key=True)
    course_id = Column(Integer)
    max_record = Column(Integer)
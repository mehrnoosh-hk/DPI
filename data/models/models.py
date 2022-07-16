from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, JSON, ForeignKey
from sqlalchemy.orm import declarative_base, relationship
from data.database import Base




class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    email = Column(String(255), nullable=False)
    password = Column(String(255), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    user_courses = relationship('UserCourse', back_populates='user')


class UserCourse(Base):
    __tablename__ = 'user_courses'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    course_name = Column(String, nullable=False)
    table_name = Column(String, nullable=False)
    course_details = Column(JSON)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    course_link=Column(String)

    user = relationship('User', back_populates='user_courses')

class Utility(Base):
    __tablename__ = 'utility'
    id = Column(Integer, primary_key=True)
    course_id = Column(Integer)
    max_record = Column(Integer)


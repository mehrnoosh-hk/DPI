import itertools
import json
import sqlite3
from aifc import Error
from typing import Optional
from dataAdapter.database import engine
from userService.userDbModel import User
from .courseDbModel import UserCourse, Utility
from courseService.course_schema import CourseSchema, CourseSchemaUpdate
from courseService.link import create_link
from pydantic import Json
from sqlalchemy import (MetaData, String, Table, delete, insert,
                        select, create_engine, table, update, Column)
from sqlalchemy.orm import Session
from sqlalchemy.schema import CreateTable, DropTable
from courseService import db_scripts
from userService import user_crud


def db_get_user_courses(user_id, db: Session) -> list[UserCourse]:
    """This function return the list of all courses of a user based on user id

    Args:
        user_id (_type_): The id of the user
        db (Session): The database session

    Returns:
        list[UserCourse]: The list of all courses of a user
    """
    user_courses = db.query(UserCourse).filter(
        UserCourse.user_id == user_id).all()
    return user_courses


def db_get_course_by_id(course_id: int, db: Session) -> Optional[UserCourse]:
    """This function return the course details based on course id

    Args:
        course_id (int): The id of the course
        db (Session): The database session

    Returns:
        UserCourse | None: The course details if the course exists, otherwise return None
    """
    course: UserCourse | None = db.query(UserCourse).filter(
        UserCourse.id == course_id).first()
    return course


def db_update_course(course_id: int, courseInfo: list[dict], db: Session) -> Optional[Error]:
    """This function updates the course details based on course id

    Args:
        course_id (int): The id of the course
        courseinfo (dict): The course details which specified by the user in the form of a dictionary
        db (Session): The database session
    """
    try:
        course = db.query(UserCourse).filter(
            UserCourse.id == course_id).first()
        temp = course.course_info
        course.course_info = list(itertools.chain([courseInfo]+temp))
        db.commit()
        return
    except Exception as e:
        return e


def db_get_course_by_name(table_name: str, db: Session) -> Optional[UserCourse]:
    course = db.query(UserCourse).filter(
        UserCourse.table_name == table_name).first()
    return course


def db_get_all_courses(db: Session):
    course = db.query(UserCourse).all()
    return course


def db_get_course_link(course_link: str, db: Session):
    course = db.query(UserCourse).filter(
        UserCourse.course_link == course_link).first()
    return course


def db_create_course(id: str, course_input: CourseSchema, db: Session) -> None:
    """Dynamically create a table for course defined by user"""
    # Create a unique name based on user_id
    TABLE_NAME = (course_input.courseName).strip().replace(" ", "_")
    # Generate Columns and columns type based on user input
    db_scripts.create_table_dynamically(
        TABLE_NAME, course_input.courseDetails, db)

    # Register the created table in user_courses table
    user_course = UserCourse(
        user_id=id,
        course_name=course_input.courseName,
        table_name=TABLE_NAME,
        course_details=course_input.courseDetails,
        course_link=create_link()
    )
    db.add(user_course)
    db.commit()
    db.refresh(user_course)
    return user_course.id


def db_get_course_details(id: int, db: Session):
    course: UserCourse = db.query(UserCourse).filter(UserCourse.id == id).first()
    table_name = course.table_name

    # Read table meta data of columns name and type and create courseFiled list
    table_meta = Table(table_name, MetaData(), autoload_with=engine)
    courseField = [{"fieldName": c.name, "fieldType": str(
        c.type)} for c in table_meta.columns]
    cleanCourseField = db_scripts.clean_up_course_fields(courseField)

    # Read table rows and create courseInfo
    stmt = select(table_meta)
    rows = db.execute(stmt).all()
    courseInfo = []
    cleanCourseInfo = []
    if len(rows) > 0:
        for row in rows:
            for i in range(len(table_meta.columns)):
                temp = {
                    "fieldName": table_meta.columns[i].name,
                    "fieldType": str(table_meta.columns[i].type),
                    "fieldValue": row[i]
                }
                courseInfo.append(temp)
        cleanCourseInfo = db_scripts.clean_up_course_fields(courseInfo)
    print(course.course_details)
    return cleanCourseInfo, cleanCourseField


def db_course_insert(table_name: str, info: list, db: Session, c_id: int, recordID: dict = None):
    # Create sqlalchemy table object
    table_meta = Table(table_name, MetaData(), autoload_with=engine)
    value = {}
    for d in info:
        value.update({d["fieldName"]: d["fieldValue"]})
    value_list = [value]
    
    # Updating an existing row
    if recordID:   
        with engine.connect() as conn:
            result = conn.execute(
                update(table_meta).where(table_meta.c.recordID == recordID["recordID"]),
                value_list
            )

    # Creating a new row
    else:
        # Read max_record from utility table
        course_util: Utility = db.query(Utility).filter(Utility.course_id == c_id).first()
        value.update({"recordID": course_util.max_record + 1})
        value_list = [value]
        with engine.connect() as conn:
            result = conn.execute(
                insert(table_meta),
                value_list
            )


def db_delete_course_record(table_name, record_id, db: Session, course):
    
    table_meta = Table(table_name, MetaData(), autoload_with=engine)
    with engine.connect() as conn:
            result = conn.execute(
                delete(table_meta).
                where(table_meta.c.recordID == record_id)
            )

    # Update index
    # db_scripts.reindex(table_name, record_id)

    # Update utility table
    course_util = db.query(Utility).filter(
        Utility.course_id == course.id).first()
    course_util.max_record = course_util.max_record - 1
    db.commit()
    db.refresh(course_util)


def db_update_utility_table(c_id: int, db: Session, delta: int):
    course_util = db.query(Utility).filter(
        Utility.course_id == c_id).first()
    course_util.max_record = course_util.max_record + delta
    db.commit()
    db.refresh(course_util)    


def db_add_course_to_utility(id, db: Session):
    utility_course = Utility(
        course_id=id,
        max_record=-1
    )
    db.add(utility_course)
    db.commit()
    db.refresh(utility_course)

def db_get_suscribed_courses(u_id: int, db: Session):
    user: User = db.query(User).filter(User.id == u_id).first()
    subs =  user.subscriptions
    result = []
    for courseID in subs:
        course: UserCourse = db_get_course_by_id(courseID, db)
        temp = {"courseID": course.id ,"courseName": course.course_name}
        result.append(temp)
    return result

def db_subscribe_course(u_id: int, courseList: list, db: Session):
    user = user_crud.db_get_user_by_id(u_id, db=db)
    current_subscription = user.subscriptions
    if not current_subscription:
        current_subscription = {}
    subs_dict = json.load(current_subscription)
    for item in courseList:
        if subs_dict.get(item):
            continue
        temp = {item: []}
        subs_dict.update(temp)
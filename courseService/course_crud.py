import datetime
import itertools
import json
from aifc import Error
from typing import Optional
from dataAdapter.database import engine
from userService.userDbModel import User
from courseService.courseDbModel import UserCourse, Utility
from courseService.course_schema import CourseSchema, CourseSchemaUpdate
from courseService.link import create_link
from pydantic import Json
from sqlalchemy import (MetaData, String, Table, delete, func, insert,
                        select, create_engine, table, true, update, Column)
from sqlalchemy.orm import Session
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
        course.course_info = list(itertools.chain([courseInfo] + temp))
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


def db_create_course(u_id: str, course_input: CourseSchema, db: Session) -> None:
    """Dynamically create a table for course defined by user"""
    # Create a unique name based on user_id
    table_name = course_input.courseName.strip().replace(" ", "_")

    # Create sqlalchemy table object with Columns and columns type based on user input, and save to db
    db_scripts.create_table_dynamically(
        table_name, course_input.courseDetails, db)

    # Register the created table in user_courses table
    user_course = UserCourse(
        user_id=u_id,
        course_name=course_input.courseName,
        table_name=table_name,
        course_details=course_input.courseDetails,
        course_link=create_link()
    )
    db.add(user_course)
    db.commit()


def db_get_course_details(c_id: int, db: Session):
    course: UserCourse = db.query(UserCourse).filter(
        UserCourse.id == c_id).first()
    table_name = course.table_name

    # Read table metadata of columns name and type and create courseFiled list
    table_meta = Table(table_name, MetaData(), autoload_with=engine)
    course_field = [{"fieldName": c.name, "fieldType": str(
        c.type)} for c in table_meta.columns]
    clean_course_field = db_scripts.clean_up_course_fields(course_field)

    # Read table rows and create course_info
    stmt = select(table_meta).order_by(table_meta.c.id)
    rows = db.execute(stmt).all()
    course_info = []
    clean_course_info = []
    if len(rows) > 0:
        for row in rows:
            temp = []
            for i in range(len(table_meta.columns)):
                temp.append({
                    "fieldName": table_meta.columns[i].name,
                    "fieldType": str(table_meta.columns[i].type),
                    "fieldValue": row[i]
                })
            course_info.append(temp)
    clean_course_info = db_scripts.clean_up_course_info(course_info)
    return clean_course_info, clean_course_field


# Read details of a course row with specific priority to show to user
def db_get_course_content_user(course_id: int, priority: int, db: Session):
    course: UserCourse = db_get_course_by_id(course_id, db)
    table_name = course.table_name

    # Create sqlalchemy table object
    table_meta = Table(table_name, MetaData(), autoload_with=engine)

    # Extract the field names and types
    course_field = [{"fieldName": c.name, "fieldType": str(
        c.type)} for c in table_meta.c]
    clean_course_field = db_scripts.clean_up_course_fields(course_field)

    # Read table rows  whit specific priority and create courseInfo
    # TODO: Convert to session
    with engine.connect() as conn:
        rows = conn.execute(
            select(table_meta).
            where(table_meta.c.Priority <= priority).where(table_meta.c.Priority != 0)
        ).all()
    course_info = []
    clean_course_info = []

    if not rows:
        rows = []

    if len(rows) > 0:
        for row in rows:
            temp = []
            for i in range(len(table_meta.columns)):
                temp.append({
                    "fieldName": table_meta.columns[i].name,
                    "fieldType": str(table_meta.columns[i].type),
                    "fieldValue": row[i]
                })
            course_info.append(temp)
        clean_course_info = db_scripts.clean_up_course_info(course_info)
    return clean_course_info, clean_course_field


def db_course_insert(table_name: str, info: list, db: Session, c_id: int, recordID: dict = None,
                     file_address: str = None):
    # Create sqlalchemy table object
    table_meta = Table(table_name, MetaData(), autoload_with=engine)
    value = {}

    # Reading field names and type from table object
    course_fields = [{"fieldName": c.name, "fieldType": str(
        c.type)} for c in table_meta.columns]

    # Create {key: value} for inserting data in table using sqlalchemy
    for d in info:
        if d["fieldName"] == "ترتیب نمایش":
            d["fieldName"] = "Priority"
        for f in course_fields:
            if f["fieldName"] == "fileType_" + d["fieldName"]:
                d["fieldName"] = "fileType_" + d["fieldName"]

        value.update({d["fieldName"]: d["fieldValue"]})

    value_list = [value]

    # Updating an existing row
    if recordID:
        record_id = recordID["recordID"]

        # Find row id based on recordID sent by user
        indexed_data = db.query(table_meta, func.rank().over(order_by=table_meta.c.id).label('rank'))
        id_to_update = indexed_data[record_id].id

        # Update record
        with engine.connect() as conn:
            result = conn.execute(
                update(table_meta).
                where(table_meta.c.id == id_to_update),
                value_list
            )

    # Creating a new row
    else:
        # TODO: Convert to session
        with engine.connect() as conn:
            result = conn.execute(
                insert(table_meta),
                value_list
            )


def db_delete_course_record(table_name, record_id, db: Session, course):
    table_meta = Table(table_name, MetaData(), autoload_with=engine)
    indexed_data = db.query(
        table_meta,
        func.rank() \
            .over(
            order_by=table_meta.c.id
        ) \
            .label('rank')
    )
    id_to_delete = indexed_data[record_id].id

    # Delete record
    with engine.connect() as conn:
        result = conn.execute(
            delete(table_meta).
            where(table_meta.c.id == id_to_delete)
        )
    # Update utility table
    # course_util = db.query(Utility).filter(
    #     Utility.course_id == course.id).first()
    # if course_util.max_record != -1:
    #     course_util.max_record = course_util.max_record - 1
    #     # Update index
    #     db_scripts.reindex(table_name, record_id, db)
    #     db.commit()
    #     db.refresh(course_util)


# def db_update_utility_table(c_id: int, db: Session, delta: int):
#     course_util = db.query(Utility).filter(
#         Utility.course_id == c_id).first()
#     course_util.max_record = course_util.max_record + delta
#     db.commit()
#     db.refresh(course_util)


# def db_add_course_to_utility(id, db: Session):
#     utility_course = Utility(
#         course_id=id,
#         max_record=-1
#     )
#     db.add(utility_course)
#     db.commit()
#     db.refresh(utility_course)


def db_get_subscribed_courses(u_id: int, db: Session) -> list:
    user: User = db.query(User).filter(User.id == u_id).first()
    # TODO: Add error handling
    if not user:
        pass
    subs = user.subscriptions
    if not subs:
        subs = {}
    return subs


# Add list of course IDs to user subscription list
def db_subscribe_course(u_id: int, courseList: list, db: Session):
    # Read user data from users table
    user = user_crud.db_get_user_by_id(u_id, db=db)
    subs_dict = user.subscriptions

    if not subs_dict:
        subs_dict = {}

    for item in courseList:
        # Checks if user already subscribed to this course
        if subs_dict.get(str(item)):
            continue

        # Checks if there is a course with this id
        course: UserCourse = db_get_course_by_id(item, db)
        if not course:
            continue

        today = datetime.date.today()
        temp = {item: today.strftime("%d/%m/%Y")}
        subs_dict.update(temp)
    # Update users table with new data
    db.execute(
        update(User).
        where(User.id == u_id).
        values(subscriptions=subs_dict)
    )
    db.commit()


# Get row of a course with specific priority
def db_get_courseInfo_by_priority(course_id: int, priority: int, db: Session):
    course: UserCourse = db.query(UserCourse).filter(UserCourse.id == course_id).first()
    if not course:
        raise Exception("There is no course with this ID")

    # Create sqlalchemy table object
    table_meta = Table(course.table_name, MetaData(), autoload_with=engine)
    with engine.connect() as conn:
        result = conn.execute(
            select(table_meta).
            where(table_meta.c.Priority == priority)
        ).first()
    return course.course_name, result


def db_handle_attachment(attachments: list, db: Session, course: UserCourse, user_id: int):
    # Exteract course Fields info
    table_meta = Table(course.table_name, MetaData(), autoload_with=engine)
    courseField = [{"fieldName": c.name, "fieldType": str(
        c.type)} for c in table_meta.columns]


def db_check_user_access_to_file(user_id: int, course_id: int, db: Session) -> bool:
    user: User = user_crud.db_get_user_by_id(user_id, db)
    course: UserCourse = db_get_course_by_id(course_id, db)
    subs = user.subscriptions
    if not subs:
        subs = {}
    if str(course_id) in subs:
        return True
    elif course and course.user_id == user_id:
        return True
    return False

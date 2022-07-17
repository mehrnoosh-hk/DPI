import itertools
import sqlite3
from aifc import Error
from typing import Optional

from dataAdapter.database import engine
from .courseDbModel import UserCourse, Utility
from courseService.course_schema import CourseSchema, CourseSchemaUpdate
from courseService.link import create_link
from pydantic import Json
from sqlalchemy import (MetaData, Table, select, create_engine, table)
from sqlalchemy.orm import Session
from sqlalchemy.schema import CreateTable, DropTable

from courseService.db_scripts import clean_up_course_fields, create_course_Info, create_table_dynamically, create_table_name, create_update_info, reindex


def db_get_user_courses(user_id, db: Session) -> list[UserCourse]:
    """This function return the list of all courses of a user based on user id

    Args:
        user_id (_type_): The id of the user
        db (Session): The database session

    Returns:
        list[UserCourse]: The list of all courses of a user
    """
    user_courses = db.query(UserCourse).filter(UserCourse.user_id == user_id).all()
    return user_courses


def db_get_course_by_id(course_id: int, db: Session) -> Optional[UserCourse]:
    """This function return the course details based on course id

    Args:
        course_id (int): The id of the course
        db (Session): The database session

    Returns:
        UserCourse | None: The course details if the course exists, otherwise return None
    """
    course: UserCourse| None = db.query(UserCourse).filter(UserCourse.id == course_id).first()
    return course


def db_update_course(course_id: int, courseInfo: list[dict], db: Session) -> Optional[Error]:
    """This function updates the course details based on course id

    Args:
        course_id (int): The id of the course
        courseinfo (dict): The course details which specified by the user in the form of a dictionary
        db (Session): The database session
    """
    try:
        course = db.query(UserCourse).filter(UserCourse.id == course_id).first()
        temp=course.course_info
        course.course_info =list (itertools.chain([courseInfo]+temp))  
        db.commit()
        return
    except Exception as e:
        return e


def db_get_course_by_name(table_name: str, db: Session) -> Optional[UserCourse]:
    course = db.query(UserCourse).filter(UserCourse.table_name == table_name).first()
    return course 

def db_get_all_courses(db:Session):
    course=db.query(UserCourse).all()
    return course
    
def db_get_course_link(course_link:str, db:Session):
    course=db.query(UserCourse).filter(UserCourse.course_link == course_link).first()
    return course


def db_create_course(id:str, course_input: CourseSchema, db:Session) -> None:
    """Dynamically create a table for course defined by user"""
    TABLE_NAME = create_table_name(id, course_input.courseName)
    create_table_dynamically(TABLE_NAME, course_input.courseDetails, db)


    # Register the created table in user_courses table
    user_course = UserCourse(
        user_id=id,
        course_name=course_input.courseName,
        table_name=TABLE_NAME,
        course_details=course_input.courseDetails,
        course_link= create_link()
        )
    db.add(user_course)
    db.commit()
    db.refresh(user_course)
    return user_course.id



def db_get_course_details(id: int, db:Session):
    course = db.query(UserCourse).filter(UserCourse.id == id).first()
    table_name = course.table_name

    # Read table meta data of columns name and type and create courseFiled list
    table_meta = Table(table_name, MetaData(), autoload_with=engine)
    courseField = [{"fieldName": c.name, "fieldType": str(c.type)} for c in table_meta.columns]
    cleanCourseField = clean_up_course_fields(courseField)

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
        cleanCourseInfo = clean_up_course_fields(courseInfo)

    return cleanCourseInfo, cleanCourseField

def db_course_insert(course, course_input: CourseSchemaUpdate, db: Session):
    
    # Updating an existing row
    if course_input.recordID:
        # Convert request body to database processable entities
        col_name_literal, col_value_literal =  create_update_info(course_input.courseInfo)
        record_id = course_input.recordID['recordID']
        sql = """
        UPDATE {table} SET ({cols}) = ({vals}) WHERE recordID = {id}
        """.format(table=course.table_name, cols=col_name_literal, vals=col_value_literal, id=record_id)
    
    # Creating a new row
    else:
        # Update utility table
        course_util = db.query(Utility).filter(Utility.course_id == course.id).first()
        course_util.max_record = course_util.max_record + 1
        db.commit()
        db.refresh(course_util)
        course_input.courseInfo.append({
            'fieldName': 'recordID',
            'fieldValue': course_util.max_record
        })

        # Convert request body to database processable entities
        col_name_literal, col_value_literal =  create_update_info((course_input.courseInfo))

        # Update course table
        sql = """
        INSERT INTO {table}({cols}) VALUES ({vals})
        """.format(table=course.table_name, cols=col_name_literal, vals=col_value_literal)
        
    with sqlite3.connect("testDB.db", check_same_thread=False) as conn:
        cur = conn.cursor()
        cur.executescript(sql)    


def db_delete_course_record(table_name, record_id, db: Session, course): 

    # Delete record from course table  
    stmt = f"DELETE FROM {table_name} WHERE recordID={record_id}"
    with sqlite3.connect("testDB.db", check_same_thread=False) as conn:
        cur = conn.cursor()
        cur.executescript(stmt)

    # Update index
    reindex(table_name, record_id)

    # Update utility table
    course_util = db.query(Utility).filter(Utility.course_id == course.id).first()
    course_util.max_record = course_util.max_record -1
    db.commit()
    db.refresh(course_util)


def db_add_course_to_utility(id, db: Session):
    utility_course = Utility(
        course_id = id,
        max_record = -1
    )
    db.add(utility_course)
    db.commit()
    db.refresh(utility_course)
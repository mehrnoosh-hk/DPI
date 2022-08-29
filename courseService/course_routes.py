import os
from datetime import date, datetime
from fastapi import APIRouter, Depends, Form, Header, Request, Response, UploadFile, status, HTTPException, File
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import inspect, MetaData, Table, update
from courseService.courseDbModel import UserCourse
from courseService.course_crud import db_check_user_access_to_file, db_get_course_link, db_get_courseInfo_by_priority
from courseService import course_crud
from courseService.course_schema import CourseSchema, CourseSchemaUpdate, DeleteRecord, SubscriptionSchema
from dataAdapter.database import get_db
from courseService import exception_handling
from typing import Dict
from userService.encrypt import get_user_from_token, oauth2_scheme
from userService import user_crud

from dataAdapter.database import engine
from userService.userDbModel import User

import aiofiles


# Create a router for handling course information
def course_router() -> APIRouter:
    course_router = APIRouter()

    # Create a new course for a user
    @course_router.post("/courses")
    def create_course(
            course_input: CourseSchema,
            response: Response,
            token: str = Depends(oauth2_scheme),
            db: Session = Depends(get_db),
    ):

        # Extract user information from token
        u_id, u_role = get_user_from_token(token)

        # Checks if user is an admin
        if u_role == "user":
            exception_handling.not_found_handler("شما اجازه ایجاد دوره را ندارید")

        # Create a table name for course to check if this course already exists
        table_name = course_input.courseName.strip().replace(" ", "_")

        # Checks if this course already exists
        course = course_crud.db_get_course_by_name(table_name, db)
        if course:
            exception_handling.conflict_handler("دوره دیگری با این نام وجود دارد")

        # Create dynamic table
        try:

            # Create new course
            course_crud.db_create_course(u_id, course_input, db)

            response.status_code = status.HTTP_201_CREATED
            return {
                "statusCode": status.HTTP_201_CREATED,
                "title": "Created",
                "statusText": "دوره جدید ایجاد شد",
            }
        except Exception as e:
            print(e)
            exception_handling.internal_error_handler("خظای سیستمی رخ داده است")

    @course_router.get("/files/{course_id}/{file_name}")
    def show_course_file(course_id: int, file_name: str, token: str = Depends(oauth2_scheme),
                         db: Session = Depends(get_db)):

        # Check if the user have access to files of this course
        u_id, _ = get_user_from_token(token)
        have_access = db_check_user_access_to_file(u_id, course_id, db)

        if not have_access:
            exception_handling.forbidden_handler("شما اجازه شماهده این فایل را ندارید")

        # Check if file exists
        file_exists = os.path.exists(file_name)

        if not file_exists:
            exception_handling.not_found_handler("فایل مورد نظر پیدا نشد")

        return FileResponse(file_name, media_type='application/octet-stream',
                            headers={"Content-Disposition": "attachment"})

    # Returns all courses that student/user can subscribe
    @course_router.get("/courses")
    def get_all_courses(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):

        # Extract user id from token
        try:
            u_id, u_role = get_user_from_token(token)
        except:
            exception_handling.unprocessable_token("لطفا مجدد وارد سیستم شوید")

        if u_role != "user":
            exception_handling.forbidden_handler("شما به این صفحه دسترسی ندارید")

        # Read user by id
        user: User = user_crud.db_get_user_by_id(u_id, db)
        subs = user.subscriptions
        if not subs:
            subs = {}
        courses = course_crud.db_get_all_courses(db=db)
        result = []
        for c in courses:
            if str(c.id) in subs:
                continue
            temp = {"courseName": c.course_name, "courseId": c.id}
            result.append(temp)
        # TODO: Make response comprehensive
        return result

    # Returns all courses for an admin
    @course_router.get("/user_courses")
    def get_courses_of_user(
            token: str = Depends(oauth2_scheme),
            db: Session = Depends(get_db)):
        u_id, u_role = get_user_from_token(token)
        if u_role != "admin":
            exception_handling.forbidden_handler("شما دسترسی مشاهده این صفحه را ندارید")
        courses: list[UserCourse] = course_crud.db_get_user_courses(u_id, db)
        if not courses:
            exception_handling.not_found_handler("دوره ای یافت نشد")
        for course in courses:
            course.course_link = "https://fastapi-dpi.chabk.ir/course/" + course.course_link
        return {
            "statusCode": status.HTTP_200_OK,
            "title": "Success",
            "statusText": "OK",
            "courses": courses
        }

    # Subscribe to one or more course
    @course_router.post("/subscribe")
    def subscribe_to_course(
            courseList: SubscriptionSchema,
            db: Session = Depends(get_db),
            token: str = Depends(oauth2_scheme)):

        u_id, u_role = get_user_from_token(token)

        if u_role != "user":
            exception_handling.forbidden_handler("شما اجازه ثبت نام در دوره ها را ندارید")

        course_crud.db_subscribe_course(
            u_id=u_id, courseList=courseList.courseIDList, db=db)
        # Read user by id
        user: User = user_crud.db_get_user_by_id(u_id, db)
        subs = user.subscriptions
        if not subs:
            subs = {}
        courses = course_crud.db_get_all_courses(db=db)
        result = []
        for c in courses:
            if str(c.id) in subs:
                continue
            temp = {"courseName": c.course_name, "courseId": c.id}
            result.append(temp)
        return {
            "statusCode": status.HTTP_200_OK,
            "title": "Success",
            "newList": result,
            "statusText": "ثبت نام با موفقیت انجام شد",
        }

    # Returns all courses that a user subscribed
    @course_router.get("/subscribe")
    def get_user_subscribed_courses(
            token: str = Depends(oauth2_scheme),
            db: Session = Depends(get_db)):
        u_id, u_role = get_user_from_token(token)
        if u_role != "user":
            exception_handling.forbidden_handler("تنها دانشجو اجازه مشاهده دوره های ثبت نامی را دارد")

        subs: dict = course_crud.db_get_subscribed_courses(u_id, db)

        # Return details of each subscribed course
        subs_info = []
        for k, _ in subs.items():
            course_id = int(k)
            course: UserCourse = course_crud.db_get_course_by_id(course_id=course_id, db=db)
            temp = {"courseName": course.course_name, "courseID": course_id}
            subs_info.append(temp)

        return {
            "statusCode": status.HTTP_200_OK,
            "title": "Success",
            "statusText": "OK",
            "course": subs_info
        }

    # Returns a course details by id for both admin and user
    @course_router.get("/courses/{course_id}")
    def get_course_details(
            course_id: int,
            db: Session = Depends(get_db),
            token: str = Depends(oauth2_scheme)):
        user_id, user_role = get_user_from_token(token)
        course = course_crud.db_get_course_by_id(course_id, db)

        if not course:
            exception_handling.not_found_handler("دوره ای با این مشخصات وجود ندارد")

        info, field = course_crud.db_get_course_details(course.id, db)

        # The case that role is admin, return all data
        if user_role == "admin":
            if course.user_id != user_id:
                exception_handling.forbidden_handler("شمااجازه مشاهده این دوره راندارید")

            return {
                "statusCode": status.HTTP_200_OK,
                "title": "Success",
                "statusText": "OK",
                "course": {
                    "courseName": course.course_name,
                    "id": course.id,
                    "created_at": course.created_at,
                    "course_link": "https://fastapi-dpi.chabk.ir/course/" + course.course_link,
                    "courseField": field,
                    "courseInfo": info}}

        # The case that role is user return row with specific priority
        user: User = user_crud.db_get_user_by_id(user_id, db)

        # Read the subscription date of this course

        sub_date_str = user.subscriptions[str(course_id)]

        sub_date = datetime.strptime(sub_date_str, "%d/%m/%Y")
        delta = datetime.today() - sub_date
        priority = delta.days + 1
        # Calculate Priority
        result_info, result_fields = course_crud.db_get_course_content_user(
            course_id=course.id,
            priority=priority,
            db=db
        )
        return {
            "statusCode": status.HTTP_200_OK,
            "title": "Success",
            "statusText": "OK",
            "course": {
                "courseName": course.course_name,
                "id": course.id,
                "created_at": course.created_at,
                "courseField": result_fields,
                "courseInfo": result_info
            }
        }

    # Add data to course
    @course_router.put("/courses/{course_id}")
    async def add_row_to_course(
            course_id: int,
            request: Request,
            db: Session = Depends(get_db),
            token: str = Depends(oauth2_scheme),
    ):

        # Read user id from token
        user_id, user_role = get_user_from_token(token)

        # Check if the role is admin
        if user_role != "admin":
            exception_handling.forbidden_handler("شما اجازه تغییر این دوره را ندارید")

        # Check if the course exists
        course: UserCourse = course_crud.db_get_course_by_id(course_id, db)
        if not course:
            exception_handling.not_found_handler("دوره ای پیدا نشد")

        # Check if user is the owner of the course
        if course.user_id != user_id:
            exception_handling.forbidden_handler("شما اجازه تغییر این دوره را ندارید")

        # Read request data
        form_data = await request.form()

        # Create courseInput from form_data
        course_input = form_data.get("courseInput")
        course_input = CourseSchemaUpdate.parse_raw(course_input)
        course_info = course_input.courseInfo

        for k, v in form_data.items():
            print("key: ", k)
            print("value: ", form_data.getlist(k))

        for f_key, f_value in form_data.items():
            if f_key == "courseInput":
                continue
            field_name = f_key
            field_value_list = form_data.getlist(f_key)
            field_value = []
            for f in field_value_list:
                async with aiofiles.open(f.filename, 'wb') as out_file:
                    content = await f.read()  # async read
                    await out_file.write(content)  # async write
                    field_value.append(f.filename)
            course_info.append({"fieldName": field_name, "fieldValue": field_value})

        try:
            # Update course table
            course_crud.db_course_insert(
                table_name=course.table_name,
                info=course_info,
                db=db,
                c_id=course.id,
                recordID=course_input.recordID
            )

            return {
                "statusCode": status.HTTP_200_OK,
                "title": "Success",
                "statusText": "دوره با موفقیت به روز رسانی شد",
            }
        except Exception as e:
            print(e)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "statusCode": status.HTTP_400_BAD_REQUEST,
                    "title": "Bad Request",
                    "errorText": "اطلاعات ارسالی با ساختار دوره همخوانی ندارد"})

    @course_router.get("/course/{course_link}")
    def get_course_by_link(course_link: str, db: Session = Depends(get_db)):
        course: UserCourse = db_get_course_link(course_link, db)
        if not course:
            exception_handling.not_found_handler("دوره ای با این مشخصات پیدا نشد")

        result_Info, result_Fields = course_crud.db_get_course_details(course.id, db)
        return {
            "statusCode": status.HTTP_200_OK,
            "title": "Success",
            "statusText": "OK",
            "course": {
                "courseName": course.course_name,
                "id": course.id,
                "created_at": course.created_at,
                "courseField": result_Fields,
                "courseInfo": result_Info
            }
        }


        exception_handling.forbidden_handler("شما اجازه مشاهده این دوره را ندارید")

    # Delete a row from a course
    @course_router.delete("/courses/{course_id}")
    def delete_course(
            course_id: int,
            id: DeleteRecord,
            db: Session = Depends(get_db),
            token: str = Depends(oauth2_scheme)):
        user_id, _ = get_user_from_token(token)
        course = course_crud.db_get_course_by_id(course_id, db)
        if not course:
            exception_handling.not_found_handler("دوره ای با این مشخصات وجود ندارد")

        if course.user_id != user_id:
            exception_handling.forbidden_handler("شما اجازه تغییر این دوره را ندارید")

        table_name = course.table_name
        course_crud.db_delete_course_record(
            table_name, id.recordID['recordID'], db, course)
        return {
            "statusCode": status.HTTP_200_OK,
            "title": "Success",
            "statusText": "ردیف با موفقیت حذف شد",
        }

    return course_router

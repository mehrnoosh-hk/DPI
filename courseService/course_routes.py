from datetime import date, datetime
from fastapi import APIRouter, Depends, Form, Response, UploadFile, status, HTTPException, File
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import inspect, MetaData, Table, update
from courseService.courseDbModel import UserCourse
from courseService.course_crud import db_get_course_link, db_get_courseInfo_by_priority
from courseService import course_crud
from courseService.course_schema import CourseSchema, CourseSchemaUpdate, DeleteRecord, SubscriptionSchema
from dataAdapter.database import get_db

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

        # Exteract user information from token
        u_id, u_role = get_user_from_token(token)

        # Checks if user is an admin
        print(u_role)
        if u_role == "user":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "statusCode": status.HTTP_403_FORBIDDEN,
                    "title": "Conflict",
                    "errorText": "شما دسترسی ایجاد دوره ندارید",
                }
            )

        # Create a table name for course to check if this course already exists
        table_name = (course_input.courseName).strip().replace(" ", "_")

        # Cheks if this course already exists
        course = course_crud.db_get_course_by_name(table_name, db)
        if course:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "statusCode": status.HTTP_409_CONFLICT,
                    "title": "Conflict",
                    "errorText": "دوره دیگری با این نام وجود دارد",
                }
            )

        # Create dynamic table
        try:
            # Create new course
            course_id = course_crud.db_create_course(
                u_id,
                course_input,
                db
            )
            # Add course to utility table
            course_crud.db_add_course_to_utility(course_id, db)
            response.status_code = status.HTTP_201_CREATED
            return {
                "statusCode": status.HTTP_201_CREATED,
                "title": "Created",
                "statusText": "دوره جدید ایجاد شد",
            }
        except Exception as e:
            print(e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "statusCode": status.HTTP_500_INTERNAL_SERVER_ERROR,
                    "title": "Internal Server Error",
                    "errorText": "خطای سیستمی رخ داده",
                }
            )

    @course_router.get("/test")
    def get_file():
        return FileResponse("golang.png")
    
    
    # Read all courses that student/user can subscribe
    @course_router.get("/courses")
    def get_all_courses(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
        u_id, u_role = get_user_from_token(token)
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
        return result

    # Returns all courses for a user
    @course_router.get("/user_courses")
    def get_courses_of_user(
            token: str = Depends(oauth2_scheme),
            db: Session = Depends(get_db)):
        u_id, u_role = get_user_from_token(token)
        courses = course_crud.db_get_user_courses(u_id, db)
        if not courses:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "statusCode": status.HTTP_404_NOT_FOUND,
                    "title": "Not Found",
                    "statusText": "Not Found",
                    "errorText": "دوره ای یافت نشد"
                }
            )

        return {
            "statusCode": status.HTTP_200_OK,
            "title": "Success",
            "statusText": "OK",
            "courses": courses
        }

    @course_router.post("/subscribe")
    def subscribe_to_course(
            courseList: SubscriptionSchema,
            db: Session = Depends(get_db),
            token: str = Depends(oauth2_scheme)):
        u_id, u_role = get_user_from_token(token)

        if u_role != "user":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "statusCode": status.HTTP_403_FORBIDDEN,
                    "title": "Forbidden",
                    "statusText": "Forbidden",
                    "errorText": "شما اجازه ثبت نام در دوره ها را ندارید"
                }
            )

        course_crud.db_subscribe_course(
            u_id=u_id, courseList=courseList.courseIDList, db=db)
        return {
            "statusCode": status.HTTP_200_OK,
            "title": "Success",
            "statusText": "ثبت نام با موفقیت انجام شد",
        }

    @course_router.get("/subscribe")
    def get_user_subscribed_courses(
            token: str = Depends(oauth2_scheme),
            db: Session = Depends(get_db)):
        u_id, u_role = get_user_from_token(token)
        if u_role != "user":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "statusCode": status.HTTP_403_FORBIDDEN,
                    "title": "Forbidden",
                    "statusText": "Forbidden",
                    "errorText": "تنها دانشجو اجازه ثبت نام و مشاهده دوره های ثبت نامی را دارد"})

        subs: dict = course_crud.db_get_suscribed_courses(u_id, db)
        if not subs:
            subs = {}
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

    # Returns a course details by id
    @course_router.get("/courses/{course_id}")
    def get_course_details(
            course_id: int,
            db: Session = Depends(get_db),
            token: str = Depends(oauth2_scheme)):
        user_id, user_role = get_user_from_token(token)
        course = course_crud.db_get_course_by_id(course_id, db)

        if not course:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "statusCode": status.HTTP_404_NOT_FOUND,
                    "title": "Not Found",
                    "statusText": "Not Found",
                    "errorText": "دوره ای با این مشخصات وجود ندارد"
                }
            )

        info, field = course_crud.db_get_course_details(course.id, db)
        if user_role == "admin":
            if course.user_id != user_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={
                        "statusCode": status.HTTP_403_FORBIDDEN,
                        "title": "Forbidden",
                        "statusText": "Forbidden",
                        "errorText": "شمااجازه مشاهده این دوره راندارید"
                    }
                )
            return {
                "statusCode": status.HTTP_200_OK,
                "title": "Success",
                "statusText": "OK",
                "course": {
                    "courseName": course.course_name,
                    "id": course.id,
                    "created_at": course.created_at,
                    "course_link": "https://fastapi-dpi.chabk.ir/" + course.course_link,
                    "courseField": field,
                    "courseInfo": info}}
        result_Info, result_Fields = course_crud.db_get_course_content_user(
            course_id=course.id,
            priority=2,
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
                "courseField": result_Fields,
                "courseInfo": result_Info
            }
        }

    # Add data to course
    @course_router.put("/courses/{course_id}")
    async def add_row_to_course(
        course_id: int,
        attachment=File(default=None),
        courseInput=Form(...),
        db: Session = Depends(get_db),
        token: str = Depends(oauth2_scheme),
    ):

        # Read user id from token
        user_id, _ = get_user_from_token(token)

        # Check if the course exists
        course: UserCourse = course_crud.db_get_course_by_id(course_id, db)
        if not course:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "statusCode": status.HTTP_404_NOT_FOUND,
                    "title": "Not Found",
                    "statusText": "Not Found",
                    "errorText": "دوره ای پیدا نشد"
                }
            )

        # Check if user is the owner of the course
        if course.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "statusCode": status.HTTP_403_FORBIDDEN,
                    "title": "Forbidden",
                    "statusText": "Forbidden",
                    "errorText": "شما اجازه تغییر این دوره را ندارید"
                }
            )

        # Add data to course
        else:
            if attachment:
                async with aiofiles.open(attachment.filename, 'wb') as out_file:
                    content = await attachment.read()  # async read
                    await out_file.write(content)  # async write

            try:
                courseInput = CourseSchemaUpdate.parse_raw(courseInput)
            except BaseException:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail={
                        "statusCode": status.HTTP_422_UNPROCESSABLE_ENTITY,
                        "title": "Forbidden",
                        "statusText": "Forbidden",
                        "errorText": "اطلاعات ارسالی با ساختار دوره همخوانی ندارد"})
            try:
                # Update course table
                course_crud.db_course_insert(
                    table_name=course.table_name,
                    info=courseInput.courseInfo,
                    db=db,
                    c_id=course.id,
                    recordID=courseInput.recordID,
                )
                # Update utility table
                course_crud.db_update_utility_table(course.id, db, 1)

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

    @course_router.get("/{course_link}")
    def get_course_by_link(course_link: str, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
        course = db_get_course_link(course_link, db)
        if not course:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "statusCode": status.HTTP_404_NOT_FOUND,
                    "title": "Not Found",
                    "statusText": "Not Found",
                    "errorText": "دوره ای با ابن مشخصات پیدا نشد"
                }
            )
        u_id, u_role = get_user_from_token(token)
        user: User = user_crud.db_get_user_by_id(user_id=u_id, db=db)
        subs: dict = user.subscriptions
        # if not subs.get(course.id):
        #     raise HTTPException(
        #         status_code=status.HTTP_403_FORBIDDEN,
        #         detail={
        #             "statusCode": status.HTTP_403_FORBIDDEN,
        #             "title": "Not Allowed",
        #             "statusText": "Not Allowed",
        #             "errorText": "شما در این دوره ثبت نام نکرده اید"
        #         }
        #     )
        result_Info, result_Fields = course_crud.db_get_course_content_user(
            course_link=course_link,
            priority=2,
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
                "courseField": result_Fields,
                "courseInfo": result_Info
            }
        }

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
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "statusCode": status.HTTP_404_NOT_FOUND,
                    "title": "Not Found",
                    "statusText": "Not Found",
                    "errorText": "دوره ای با این مشخصات وجود ندارد"
                }
            )

        if course.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "statusCode": status.HTTP_403_FORBIDDEN,
                    "title": "Forbidden",
                    "statusText": "Forbidden",
                    "errorText": "شما اجازه تغییر این دوره را ندارید"
                }
            )

        table_name = course.table_name
        course_crud.db_delete_course_record(
            table_name, id.recordID['recordID'], db, course)
        return {
            "statusCode": status.HTTP_200_OK,
            "title": "Success",
            "statusText": "ردیف با موفقیت حذف شد",
        }
    
    

    return course_router

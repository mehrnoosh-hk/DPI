from fastapi import APIRouter, Depends, Response, UploadFile, status, HTTPException, File
from sqlalchemy.orm import Session
from sqlalchemy import inspect
from data.crud.course_crud import db_get_course_link
from data.crud import course_crud
from data.schemas.course_schema import CourseSchema, CourseSchemaUpdate, DeleteRecord
from data.database import get_db

from helper.encrypt import get_user_id_from_token, oauth2_scheme
from helper.db_scripts import create_db_name

# Create a router for handling course information
def course_router() -> APIRouter:
    course_router = APIRouter()

    # Returns all courses for a user
    @course_router.get("/user_courses")
    def get_courses_of_user(token: str = Depends(oauth2_scheme), db:Session = Depends(get_db)):
        id = get_user_id_from_token(token)
        courses = course_crud.db_get_user_courses(id, db)
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
        

    # Returns a course details by id
    @course_router.get("/courses/{course_id}")
    def get_course(course_id: int, db: Session = Depends(get_db),token: str = Depends(oauth2_scheme)):
        user_id = get_user_id_from_token(token)
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
                    "errorText": "شمااجازه مشاهده این دوره راندارید"
                }
            )
        info , field = course_crud.db_get_course_details(course.id, db)
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
                "courseInfo": info
            }
        }

    # Edits a course by id
    @course_router.put("/courses/{course_id}")
    def edit_course(
        course_id: int,
        course_input: CourseSchemaUpdate,
        db: Session = Depends(get_db),
        token: str = Depends(oauth2_scheme),
    ):
        # Checks if the course exists
        user_id = get_user_id_from_token(token)
        course = course_crud.db_get_course_by_id(course_id, db)
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
        
        # Checks if user is the owner of the course
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
            course_crud.db_course_insert(course, course_input, db)
            return {
            "statusCode": status.HTTP_200_OK,
            "title": "Success",
            "statusText": "دوره با موفقیت به روز رسانی شد",
            }

    # Create a new course for a user
    @course_router.post("/courses")
    def create_course(
                    course_input: CourseSchema,
                    response: Response,
                    token: str = Depends(oauth2_scheme),
                    db: Session = Depends(get_db),
        ):
        
        id = get_user_id_from_token(token)
        table_name = create_db_name(id, course_input.courseName)

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
            
        # Create table
        try:
            # Create new course
            course_id = course_crud.db_create_course(
                id,
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

    
    @course_router.get("/{course_link}")
    def get_course_by_link(course_link:str,db:Session=Depends(get_db)):
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
        info , field = course_crud.db_get_course_details(course.id, db)
        return {
            "statusCode": status.HTTP_200_OK,
            "title": "Success",
            "statusText": "OK",
            "course": {
                "courseName": course.course_name,
                "id": course.id,
                "created_at": course.created_at,
                "courseField": field,
                "courseInfo": info
            }
        }

    # Delete a row from a course
    @course_router.delete("/courses/{course_id}")
    def delete_course(course_id: int, id: DeleteRecord, db: Session = Depends(get_db),token: str = Depends(oauth2_scheme)):
        user_id = get_user_id_from_token(token)
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
        course_crud.db_delete_course_record(table_name, id.recordID['recordID'], db, course)
        return {
            "statusCode": status.HTTP_200_OK,
            "title": "Success",
            "statusText": "ردیف با موفقیت حذف شد",
        }

    return course_router
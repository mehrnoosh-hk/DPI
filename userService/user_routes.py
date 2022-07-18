import json
from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session
from userService.encrypt import (
    encrypt_password, 
    check_password, 
    create_token, 
    get_user_from_token, 
    oauth2_scheme
)

from userService.user_schema import UserSchema
from userService import user_crud
from dataAdapter.database import get_db
from userService import userDbModel

# Create a router for handling user authentication and information
def auth_router() -> APIRouter:
    user_router = APIRouter()

    # Handles user signup
    @user_router.post("/signup")
    def signup(user_input: UserSchema, response:Response, db: Session = Depends(get_db)):
        user = user_crud.db_get_user_by_email(user_input.email, db)
        if user:
            response.status_code = status.HTTP_409_CONFLICT
            return {
                "statusCode": status.HTTP_409_CONFLICT,
                "title": "user already exists",
                "errorMessage": "با این مشخصات حساب کاربری دیگری ایجاد شده است"
            }
        hashed_pass = encrypt_password(user_input.password)
        user_id = user_crud.db_create_user(user_input.email, hashed_pass, "user", db)
        return {
            "statusCode": status.HTTP_201_CREATED,
            "title": "Successful",
            "messsage": "حساب کاربری شما ایجاد شد",
        }

    # Handle Admin signup
    @user_router.post("/signup_admin")
    def signup_admin(user_input: UserSchema, response:Response, db: Session = Depends(get_db)):
        user = user_crud.db_get_user_by_email(user_input.email, db)
        if user:
            response.status_code = status.HTTP_409_CONFLICT
            return {
                "statusCode": status.HTTP_409_CONFLICT,
                "title": "user already exists",
                "errorMessage": "با این مشخصات حساب کاربری دیگری ایجاد شده است"
            }
        hashed_pass = encrypt_password(user_input.password)
        user_id = user_crud.db_create_user(user_input.email, hashed_pass, "admin", db)
        return {
            "statusCode": status.HTTP_201_CREATED,
            "title": "Successful",
            "messsage": "حساب کاربری شما ایجاد شد",
        }

    # Handles user login and return a token if user is valid
    @user_router.post("/login")
    def login(user_input: UserSchema, db: Session = Depends(get_db)):
        user = user_crud.db_get_user_by_email(user_input.email, db)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "statusCode": status.HTTP_403_FORBIDDEN,
                    "title": "forbidden",
                    "statusText": "نام کاربری یا رمز عبور اشتباه است"
                }
            )
        hashed_pass = encrypt_password(user_input.password)
        if not check_password(user_input.password, user.password):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "statusCode": status.HTTP_403_FORBIDDEN,
                    "title": "forbidden",
                    "statusText": "نام کاربری یا رمز عبور اشتباه است"
                }
            )
        else:
            token = create_token(user.id, user.role)
            return {
                "statusCode": status.HTTP_200_OK,
                "title": "Successful",
                "message": "خوش آمدید",
                "accessToken": token,
            }

    # Returns the list of all users
    @user_router.get("/users")
    def get_users(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
        users = user_crud.db_get_users(db)
        data = []
        for user in users:
            data.append({
                "id": user.id,
                "email": user.email,
                "creation date": user.created_at,
            })
        return {
                "statusCode": status.HTTP_200_OK,
                "title": "Success",
                "statusText": data,
            }

    # Returns details of current user
    @user_router.get("/users/me")
    def read_users_me(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
        try:
            id = get_user_from_token(token)
        
            user = user_crud.db_get_user_by_id(id, db)
            data = {
                "id": user.id,
                "email": user.email,
                "creation date": user.created_at,
            }
            return {
                    "statusCode": status.HTTP_200_OK,
                    "title": "Success",
                    "statusText": data,
                }
        except:
            return {
                    "statusCode": status.HTTP_400_BAD_REQUEST,
                    "title": "Wrong Credential",
                    "statusText": "ایمیل یا رمز عبور نادرست است"
                }

    return user_router
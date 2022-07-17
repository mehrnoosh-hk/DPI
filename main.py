from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from userService.user_routes import auth_router
from courseService.course_routes import course_router
from dataAdapter.database import Base, engine

app = FastAPI()

user_router = auth_router()
app.include_router(user_router)

course_router = course_router()
app.include_router(course_router)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(engine)

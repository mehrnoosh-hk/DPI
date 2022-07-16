from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes.user_routes.user_routes import auth_router
from routes.course_routes.course_routes import course_router

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

from fastapi import FastAPI

from src.routers import auth_router
from src.routers import student_routers, user_routers, teacher_routers
from src.routers import subject_routers, group_routers, mark_routers


app = FastAPI()


app.include_router(auth_router.router)
app.include_router(user_routers.router)
app.include_router(student_routers.router)
app.include_router(teacher_routers.router)
app.include_router(subject_routers.router)
app.include_router(group_routers.router)
app.include_router(mark_routers.router)
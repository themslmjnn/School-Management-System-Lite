from fastapi import FastAPI

from src.routers import user_router, student_router, auth_router

app = FastAPI()

app.include_router(user_router.router)
app.include_router(student_router.router)
app.include_router(auth_router.router)
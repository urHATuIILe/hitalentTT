from fastapi import APIRouter

from app.api.departments import router as departments_router
from app.api.employees import router as employees_router

api_router = APIRouter()

api_router.include_router(departments_router)
api_router.include_router(employees_router)

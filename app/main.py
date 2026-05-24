from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from loguru import logger

from app.config import settings
from app.api.router import api_router
from app.database import init_db, close_db
from app.utils.exceptions import (
    DepartmentNotFoundError,
    DuplicateDepartmentNameError,
    SelfReferenceError,
    CyclicDependencyError,
    ReassignDepartmentRequiredError,
    ReassignTargetNotFoundError,
    ReassignToSameDepartmentError,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting {settings.APP_NAME}...")
    await init_db()
    yield
    logger.info("Shutting down...")
    await close_db()


app = FastAPI(
    title=settings.APP_NAME,
    description="API для управления организационной структурой: подразделения и сотрудники",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(api_router)


@app.exception_handler(DepartmentNotFoundError)
async def department_not_found_handler(request: Request, exc: DepartmentNotFoundError):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


@app.exception_handler(DuplicateDepartmentNameError)
async def duplicate_department_handler(request: Request, exc: DuplicateDepartmentNameError):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


@app.exception_handler(SelfReferenceError)
async def self_reference_handler(request: Request, exc: SelfReferenceError):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


@app.exception_handler(CyclicDependencyError)
async def cyclic_dependency_handler(request: Request, exc: CyclicDependencyError):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


@app.exception_handler(ReassignDepartmentRequiredError)
async def reassign_required_handler(request: Request, exc: ReassignDepartmentRequiredError):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


@app.exception_handler(ReassignTargetNotFoundError)
async def reassign_target_handler(request: Request, exc: ReassignTargetNotFoundError):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


@app.exception_handler(ReassignToSameDepartmentError)
async def reassign_same_handler(request: Request, exc: ReassignToSameDepartmentError):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "ok"}

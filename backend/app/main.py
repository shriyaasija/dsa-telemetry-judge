from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.problem import router as problems_router
from app.api.auth import router as auth_router
from app.api.users import router as users_router

app = FastAPI(
    title=settings.APP_NAME,
    description="Track your problem-solving journey",
    version="0.2.0",
    debug=settings.DEBUG
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# include routers
app.include_router(auth_router, prefix=settings.API_V1_PREFIX)
app.include_router(users_router, prefix=settings.API_V1_PREFIX)
app.include_router(problems_router, prefix=settings.API_V1_PREFIX)


@app.get("/")
async def root():
    return {
        "message": f"{settings.APP_NAME} API",
        "version": "0.2.0",
        "status": "healthy",
        "environment": settings.ENVIRONMENT,
        "features": ["problems", "authentication", "user-management"]
    }


@app.get("/health")
async def health_check():
    return {"status": "ok", "database": "connected"}
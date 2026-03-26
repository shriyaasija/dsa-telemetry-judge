from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.problem import router as problems_router
from app.api.auth import router as auth_router
from app.api.users import router as users_router
from app.api.attempts import router as attempts_router
from app.api.telemetry import router as telemetry_router
from app.core.redis import RedisService
from app.api.dashboard import router as dashboard_router


app = FastAPI(
    title=settings.APP_NAME,
    description="Track your problem-solving journey with telemetry",
    version="0.4.0",
    debug=settings.DEBUG,
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    """Connect to Redis on startup."""
    try:
        await RedisService.connect()
        print("Redis connected")
    except Exception as e:
        print(f"Redis connection failed: {e} (caching disabled)")


@app.on_event("shutdown")
async def shutdown_event():
    """Disconnect from Redis on shutdown."""
    await RedisService.disconnect()
    print("Redis disconnected")

# Include routers
app.include_router(auth_router, prefix=settings.API_V1_PREFIX)
app.include_router(users_router, prefix=settings.API_V1_PREFIX)
app.include_router(problems_router, prefix=settings.API_V1_PREFIX)
app.include_router(attempts_router, prefix=settings.API_V1_PREFIX)
app.include_router(telemetry_router, prefix=settings.API_V1_PREFIX)
app.include_router(dashboard_router, prefix=settings.API_V1_PREFIX)

@app.get("/")
async def root():
    return {
        "message": f"{settings.APP_NAME} API",
        "version": "0.4.0",
        "status": "healthy",
        "environment": settings.ENVIRONMENT,
        "features": ["problems", "auth", "attempts", "telemetry", "dashboard"],
    }
    
@app.get("/health")
async def health_check():
    redis_status = "connected"
    try:
        from app.core.redis import RedisService
        client = RedisService.get_client()
        await client.ping()
    except Exception:
        redis_status = "disconnected"
    return {"status": "ok", "database": "connected", "redis": redis_status}
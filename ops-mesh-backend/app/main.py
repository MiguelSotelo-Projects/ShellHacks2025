from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from app.core.config import settings
from app.api import appointments, walkin, checkin, dashboard, queue

# Create FastAPI instance
app = FastAPI(
    title="Ops Mesh - Patient Check-In API",
    description="Hospital patient check-in system with Google ADK agents",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "ops-mesh-backend"}

# Include API routers
app.include_router(appointments.router, prefix="/api", tags=["appointments"])
app.include_router(walkin.router, prefix="/api", tags=["walk-in"])
app.include_router(checkin.router, prefix="/api", tags=["check-in"])
app.include_router(dashboard.router, prefix="/api", tags=["dashboard"])
app.include_router(queue.router, prefix="/api", tags=["queue"])

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": str(exc) if settings.DEBUG else "Something went wrong"
        }
    )

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "Ops Mesh - Patient Check-In API",
        "version": "1.0.0",
        "docs": "/docs"
    }

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
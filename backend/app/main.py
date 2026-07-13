import os
import logging
# pyrefly: ignore [missing-import]
from fastapi import FastAPI
# pyrefly: ignore [missing-import]
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.api.auth import router as auth_router
from app.api.docking import router as docking_router
from app.api.prediction import router as prediction_router

# Configure Logger
logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# Initialize FastAPI App
app = FastAPI(
    title=settings.APP_NAME,
    description="Backend API services for Quantum PharmX Molecular Docking and Binding Affinity Prediction.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS Middlewares
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register Routers
app.include_router(auth_router)
app.include_router(docking_router)
app.include_router(prediction_router)

@app.on_event("startup")
async def startup_event():
    logger.info("Initializing Quantum PharmX Backend...")
    
    # 1. Create upload and output directory structures
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    os.makedirs(settings.OUTPUT_DIR, exist_ok=True)
    logger.info(f"Directory check: '{settings.UPLOAD_DIR}' and '{settings.OUTPUT_DIR}' folders prepared.")

    # 2. Automatically generate database schema tables on startup for zero-config run
    try:
        from app.database import async_engine, Base
        import app.models  # Force models import to register with Base
        
        async with async_engine.begin() as conn:
            # Drop tables or create if they do not exist
            await conn.run_sync(Base.metadata.create_all)
            
        logger.info("Database schema tables verified and created successfully.")
    except Exception as e:
        logger.error(f"Error initializing database tables on startup: {str(e)}")

@app.get("/", tags=["General"])
async def root():
    return {
        "app": settings.APP_NAME,
        "status": "online",
        "documentation": "/docs"
    }

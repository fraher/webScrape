from fastapi import FastAPI
from app.routes import files

app = FastAPI(title="My FastAPI Project")

# Include routers
app.include_router(files.router, prefix="/files", tags=["Files"])
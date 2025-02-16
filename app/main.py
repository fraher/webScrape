from fastapi import FastAPI
from app.routes import find, extract

app = FastAPI(title="My FastAPI Project")

# Include routers
app.include_router(find.router, prefix="/find", tags=["Find"])
app.include_router(extract.router, prefix="/extract", tags=["Extract"])

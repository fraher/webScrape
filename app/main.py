from fastapi import FastAPI
from app.routes import files

app = FastAPI(title="Web Scraper API", description="API to scrape webpages for PDF files and extract tables from them.")

# Include routers
app.include_router(files.router, prefix="/files", tags=["Files"])
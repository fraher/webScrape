from fastapi import APIRouter
from app.services.webscraper import WebScraper
from pydantic import BaseModel
from app.models import FileType

router = APIRouter()

class WebScrapeRequest(BaseModel):
    url: str
    type: FileType    
    css_selector: str = None
    

@router.post("/")
async def post(request: WebScrapeRequest):
    scraper = WebScraper(request)
    return {"urls": scraper.scrape()}    

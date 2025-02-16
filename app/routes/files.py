from fastapi import APIRouter
from app.services.webscraper import WebScraper
from pydantic import BaseModel
from app.models import FileType, DataType, OutputFormat
from fastapi import Request
from app.services.pdfextractor import PDFExtractor
from fastapi.responses import StreamingResponse

router = APIRouter()

class DiscoverRequest(BaseModel):
    url: str
    type: FileType = FileType.PDF    
    data_type: DataType = DataType.Tables
    css_selector: str = None # User has option to provide a CSS selector to filter to a specific section of the page

class ExtractRequest(BaseModel):
    document_urls: list[str] = None
    data_type: DataType = DataType.Tables
    output_format: str = OutputFormat.CSV
    single_file: bool = True

class CollectRequest(BaseModel):
    discover: DiscoverRequest    
    extract: ExtractRequest

@router.post("/discover")
async def post(request: DiscoverRequest):
    """Discover PDF files on a webpage and return the URLs."""
    scraper = WebScraper(request)
    urls = scraper.scrape()
    return {"document_urls": urls}    

@router.post("/extract")
async def post(request: ExtractRequest):
    """Extract tables from PDF files given a list of URLs."""
    if request.document_urls is None:
        return {"error": "No document URLs provided."}
    if request.data_type == DataType.Tables: # Additional types can be added here
        extractor = PDFExtractor()
    else:
        return {"error": "Data type not supported."}
    try:
        buffer, media_type, headers = extractor.extract(request.document_urls, request.output_format)
        return StreamingResponse(buffer, media_type=media_type, headers=headers)    
    except Exception as e:
        return {"error": str(e)}
    
@router.post("/collect")
async def post(request: CollectRequest):
    """Discover PDF files on a webpage and extract tables from them."""
    scraper = WebScraper(request.discover)
    urls = scraper.scrape()

    if request.extract.data_type == DataType.Tables: # Additional types can be added here
        extractor = PDFExtractor()
    else:
        return {"error": "Data type not supported."}
    try:
        buffer, media_type, headers = extractor.extract(urls, request.extract.output_format)
        return StreamingResponse(buffer, media_type=media_type, headers=headers)    
    except Exception as e:
        return {"error": str(e)}

    

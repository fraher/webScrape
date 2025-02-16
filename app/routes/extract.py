from fastapi import APIRouter
from fastapi import Request
from pydantic import BaseModel
from app.services.pdfextractor import PDFExtractor
from fastapi.responses import StreamingResponse

router = APIRouter()

class PDFTablesRequest(BaseModel):
    urls: list

@router.post("/pdf_tables")
async def post(request: PDFTablesRequest):
    extractor = PDFExtractor()
    try:
        buffer, media_type, headers = extractor.extract(request.urls)
        return StreamingResponse(buffer, media_type=media_type, headers=headers)    
    except Exception as e:
        return {"error": str(e)}
    
    

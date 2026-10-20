import shutil
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, status
from backend.app.core.config import settings
from backend.app.core.logger import logger
from backend.app.core.security import ClearanceLevel, Department
from backend.app.schemas.document import DocumentUploadMetadata, IngestResponse
from backend.app.services.pdf_loader import PDFLoaderService
from backend.app.services.chunker import DocumentChunkerService
from backend.app.services.vector_store import vector_store_service

router = APIRouter(prefix="/api/ingest", tags=["Ingestion"])
chunker = DocumentChunkerService()

@router.post("/upload", response_model=IngestResponse)
async def upload_pdf(
    file: UploadFile = File(...),
    department: Department = Form(default=Department.GENERAL),
    access_level: ClearanceLevel = Form(default=ClearanceLevel.INTERNAL),
    category: str = Form(default="Standard")
):
    """
    Uploads an internal enterprise PDF, extracts text per page, chunks with
    metadata, generates embeddings, and saves to FAISS vector store.
    """
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF documents are supported for ingestion."
        )

    upload_dir = Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)
    saved_path = upload_dir / file.filename

    # Save uploaded file to disk
    try:
        with open(saved_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        logger.error(f"Failed to save uploaded file '{file.filename}': {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not save uploaded file: {str(e)}"
        )

    # Parse PDF using PyMuPDF
    try:
        pdf_data = PDFLoaderService.load_pdf(str(saved_path), filename=file.filename)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Failed to parse PDF: {str(e)}"
        )

    # Chunk with metadata
    meta = DocumentUploadMetadata(
        department=department,
        access_level=access_level,
        category=category
    )
    chunks = chunker.chunk_pdf(pdf_data, meta)

    if not chunks:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No readable text found in PDF."
        )

    # Index into FAISS
    try:
        vector_store_service.add_document_chunks(
            document_id=pdf_data.document_id,
            filename=pdf_data.filename,
            chunks=chunks,
            department=department.value,
            access_level=access_level.value,
            category=category,
            total_pages=pdf_data.total_pages,
            file_size_bytes=pdf_data.file_size
        )
    except Exception as e:
        logger.error(f"Failed to index chunks for '{file.filename}': {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to index document in vector store: {str(e)}"
        )

    return IngestResponse(
        success=True,
        document_id=pdf_data.document_id,
        filename=pdf_data.filename,
        total_pages=pdf_data.total_pages,
        total_chunks=len(chunks),
        message=f"Successfully ingested and indexed '{pdf_data.filename}' into FAISS."
    )

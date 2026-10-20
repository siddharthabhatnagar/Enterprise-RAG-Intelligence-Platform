import os
import sys
from pathlib import Path

# Add project root to path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from backend.app.core.security import ClearanceLevel, Department
from backend.app.schemas.document import DocumentUploadMetadata
from backend.app.services.pdf_loader import PDFLoaderService
from backend.app.services.chunker import DocumentChunkerService
from backend.app.services.vector_store import vector_store_service
from backend.app.core.logger import logger

SAMPLE_DOCS_CONFIG = [
    {
        "filename": "Employee_Handbook_General_Policy.pdf",
        "department": Department.GENERAL,
        "access_level": ClearanceLevel.PUBLIC,
        "category": "Corporate Policy"
    },
    {
        "filename": "Engineering_Cloud_Infrastructure.pdf",
        "department": Department.ENGINEERING,
        "access_level": ClearanceLevel.INTERNAL,
        "category": "Architecture"
    },
    {
        "filename": "Q3_Confidential_Financial_Audit.pdf",
        "department": Department.FINANCE,
        "access_level": ClearanceLevel.CONFIDENTIAL,
        "category": "Financial Report"
    },
    {
        "filename": "HR_Executive_Compensation_2026.pdf",
        "department": Department.HR,
        "access_level": ClearanceLevel.RESTRICTED,
        "category": "Executive Compensation"
    }
]

def seed_sample_documents():
    """Seeds the FAISS vector database with built-in enterprise PDFs."""
    sample_dir = ROOT_DIR / "sample_docs"
    chunker = DocumentChunkerService()

    total_indexed = 0
    for doc_cfg in SAMPLE_DOCS_CONFIG:
        pdf_path = sample_dir / doc_cfg["filename"]
        if not pdf_path.exists():
            logger.warning(f"File not found: {pdf_path}")
            continue

        try:
            pdf_data = PDFLoaderService.load_pdf(str(pdf_path), filename=doc_cfg["filename"])
            meta = DocumentUploadMetadata(
                department=doc_cfg["department"],
                access_level=doc_cfg["access_level"],
                category=doc_cfg["category"]
            )
            chunks = chunker.chunk_pdf(pdf_data, meta)

            vector_store_service.add_document_chunks(
                document_id=pdf_data.document_id,
                filename=pdf_data.filename,
                chunks=chunks,
                department=doc_cfg["department"].value,
                access_level=doc_cfg["access_level"].value,
                category=doc_cfg["category"],
                total_pages=pdf_data.total_pages,
                file_size_bytes=pdf_data.file_size
            )
            total_indexed += len(chunks)
            logger.info(f"Indexed sample doc '{doc_cfg['filename']}' ({len(chunks)} chunks)")
        except Exception as e:
            logger.error(f"Failed to seed '{doc_cfg['filename']}': {e}")

    logger.info(f"Seeding completed. Total chunks indexed: {total_indexed}")
    return total_indexed

if __name__ == "__main__":
    seed_sample_documents()

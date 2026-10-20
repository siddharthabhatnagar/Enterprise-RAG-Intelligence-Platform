import fitz  # PyMuPDF
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional
from backend.app.core.logger import logger

class PDFPageData:
    def __init__(self, page_number: int, text: str):
        self.page_number = page_number
        self.text = text

class PDFDocumentData:
    def __init__(self, document_id: str, filename: str, pages: List[PDFPageData], file_size: int):
        self.document_id = document_id
        self.filename = filename
        self.pages = pages
        self.file_size = file_size
        self.total_pages = len(pages)

class PDFLoaderService:
    """Extracts clean text and page-level metadata from PDF documents using PyMuPDF."""

    @staticmethod
    def load_pdf(file_path: str, filename: Optional[str] = None) -> PDFDocumentData:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"PDF file not found at: {file_path}")

        doc_name = filename or path.name
        doc_id = hashlib.sha256(f"{doc_name}_{path.stat().st_size}".encode()).hexdigest()[:12]

        pages: List[PDFPageData] = []
        try:
            with fitz.open(file_path) as doc:
                for page_idx, page in enumerate(doc):
                    text = page.get_text("text").strip()
                    # Fallback or clean up text
                    if text:
                        # Clean multiple spaces and blank line spam
                        cleaned_lines = [line.strip() for line in text.splitlines() if line.strip()]
                        cleaned_text = "\n".join(cleaned_lines)
                        pages.append(PDFPageData(page_number=page_idx + 1, text=cleaned_text))
                    else:
                        # Empty page or scanned image
                        pages.append(PDFPageData(page_number=page_idx + 1, text="[Empty or Scanned Page]"))

            logger.info(f"Loaded PDF '{doc_name}' with {len(pages)} pages (Document ID: {doc_id})")
            return PDFDocumentData(
                document_id=doc_id,
                filename=doc_name,
                pages=pages,
                file_size=path.stat().st_size
            )
        except Exception as e:
            logger.error(f"Error loading PDF '{file_path}': {str(e)}")
            raise e

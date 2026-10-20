from typing import List, Dict, Any
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from backend.app.services.pdf_loader import PDFDocumentData
from backend.app.schemas.document import DocumentUploadMetadata
from backend.app.core.logger import logger

class DocumentChunkerService:
    """Splits PDF pages into semantic chunks while strictly maintaining page-level metadata."""

    def __init__(self, chunk_size: int = 650, chunk_overlap: int = 100):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=["\n\n", "\n", ". ", " ", ""],
            keep_separator=True
        )

    def chunk_pdf(self, pdf_doc: PDFDocumentData, metadata: DocumentUploadMetadata) -> List[Document]:
        langchain_docs: List[Document] = []
        global_chunk_idx = 0

        for page in pdf_doc.pages:
            if not page.text or page.text == "[Empty or Scanned Page]":
                continue

            # Split text on this specific page
            page_chunks = self.splitter.split_text(page.text)

            for chunk_idx, text_chunk in enumerate(page_chunks):
                chunk_id = f"{pdf_doc.document_id}_p{page.page_number}_c{chunk_idx}"

                doc = Document(
                    page_content=text_chunk,
                    metadata={
                        "chunk_id": chunk_id,
                        "document_id": pdf_doc.document_id,
                        "document_name": pdf_doc.filename,
                        "page_number": page.page_number,
                        "total_pages": pdf_doc.total_pages,
                        "department": metadata.department.value,
                        "access_level": metadata.access_level.value,
                        "category": metadata.category or "General",
                        "tags": metadata.tags or [],
                        "file_size": pdf_doc.file_size,
                        "global_index": global_chunk_idx
                    }
                )
                langchain_docs.append(doc)
                global_chunk_idx += 1

        logger.info(
            f"Chunked '{pdf_doc.filename}' ({pdf_doc.total_pages} pages) into "
            f"{len(langchain_docs)} chunks (size={self.chunk_size}, overlap={self.chunk_overlap})"
        )
        return langchain_docs

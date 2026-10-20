from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException, status
from backend.app.services.vector_store import vector_store_service
from backend.app.schemas.document import DocumentRecord

router = APIRouter(prefix="/api/documents", tags=["Documents"])

@router.get("", response_model=List[DocumentRecord])
async def list_documents():
    """Lists all ingested enterprise documents in the knowledge base."""
    return vector_store_service.list_documents()

@router.get("/{document_id}/chunks", response_model=List[Dict[str, Any]])
async def get_document_chunks(document_id: str):
    """Retrieves all indexed chunks for a given document for inspection."""
    chunks = vector_store_service.get_document_chunks(document_id)
    if not chunks:
        # Check if doc exists in registry
        docs = vector_store_service.list_documents()
        if not any(d.document_id == document_id for d in docs):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document '{document_id}' not found."
            )
    return chunks

@router.delete("/{document_id}")
async def delete_document(document_id: str):
    """Deletes a document and its chunks from the knowledge base."""
    success = vector_store_service.delete_document(document_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document '{document_id}' not found."
        )
    return {"success": True, "message": f"Document '{document_id}' deleted successfully."}

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from backend.app.core.security import ClearanceLevel, Department

class DocumentUploadMetadata(BaseModel):
    department: Department = Field(default=Department.GENERAL, description="Owning department")
    access_level: ClearanceLevel = Field(default=ClearanceLevel.INTERNAL, description="Security clearance level")
    category: Optional[str] = Field(default="Standard", description="Document category/tag")
    tags: Optional[List[str]] = Field(default=[], description="Custom labels")

class DocumentChunk(BaseModel):
    chunk_id: str
    document_id: str
    document_name: str
    page_number: int
    content: str
    department: str
    access_level: str
    category: str
    score: Optional[float] = None
    rerank_score: Optional[float] = None

class DocumentRecord(BaseModel):
    document_id: str
    filename: str
    total_pages: int
    total_chunks: int
    department: str
    access_level: str
    category: str
    file_size_bytes: int
    uploaded_at: str

class IngestResponse(BaseModel):
    success: bool
    document_id: str
    filename: str
    total_pages: int
    total_chunks: int
    message: str

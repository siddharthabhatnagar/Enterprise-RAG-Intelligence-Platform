from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class Citation(BaseModel):
    document_name: str
    page_number: int
    department: str
    access_level: str
    relevance_score: float
    excerpt: str
    chunk_id: str

class LatencyBreakdown(BaseModel):
    retrieval_ms: float = 0.0
    rerank_ms: float = 0.0
    llm_generation_ms: float = 0.0
    total_ms: float = 0.0

class GroundingEvaluation(BaseModel):
    score: float = 100.0
    verdict: str = "HIGH"
    hallucination_risk: str = "Minimal"
    supported_claims_ratio: float = 1.0
    reasoning: str = "All key statements are directly cited from retrieved source documents."

class QueryRequest(BaseModel):
    query: str = Field(..., description="The employee's natural language question")
    user_id: str = Field(default="admin", description="Active user profile ID for RBAC enforcement")
    department_filter: Optional[str] = Field(default=None, description="Optional filter by department")
    include_debug_chunks: bool = Field(default=True, description="Whether to include retrieved candidate chunks for inspection")

class QueryResponse(BaseModel):
    query: str
    answer: str
    citations: List[Citation]
    latency: LatencyBreakdown
    grounding: GroundingEvaluation
    user_context: Dict[str, Any]
    chunks_retrieved_count: int
    chunks_used_count: int
    debug_chunks: Optional[List[Dict[str, Any]]] = None

from fastapi import APIRouter, HTTPException, status
from backend.app.schemas.query import QueryRequest, QueryResponse
from backend.app.core.security import DEMO_USERS, User, Role, Department, ClearanceLevel
from backend.app.services.rag_chain import rag_chain
from backend.app.core.logger import logger

router = APIRouter(prefix="/api/query", tags=["Query & RAG"])

@router.post("", response_model=QueryResponse)
async def query_intelligence_platform(request: QueryRequest):
    """
    Submits a query to the enterprise RAG platform with document-level RBAC,
    cross-encoder reranking, strict grounding, and structured citations.
    """
    if not request.query.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Query string cannot be empty."
        )

    # Resolve active user identity
    user_id = request.user_id.lower()
    user = DEMO_USERS.get(user_id)

    if not user:
        # Default to standard employee if user profile key is unknown
        logger.warning(f"User ID '{request.user_id}' not found in registry. Defaulting to general employee.")
        user = User(
            user_id=request.user_id,
            name=f"Employee ({request.user_id})",
            role=Role.EMPLOYEE,
            department=Department.GENERAL,
            custom_clearance=ClearanceLevel.INTERNAL
        )

    try:
        response = rag_chain.answer_query(request=request, user=user)
        return response
    except Exception as e:
        logger.error(f"Error handling query: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal RAG pipeline error: {str(e)}"
        )

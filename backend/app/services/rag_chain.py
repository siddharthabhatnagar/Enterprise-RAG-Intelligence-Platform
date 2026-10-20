import time
from typing import List, Dict, Any, Optional, Tuple
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.documents import Document
from backend.app.core.config import settings
from backend.app.core.logger import logger
from backend.app.core.security import User
from backend.app.services.vector_store import vector_store_service
from backend.app.services.reranker import reranker_service
from backend.app.services.hallucination import hallucination_service
from backend.app.schemas.query import (
    QueryRequest, QueryResponse, Citation, LatencyBreakdown, GroundingEvaluation
)

class EnterpriseRAGChain:
    """
    Core Enterprise RAG Chain built purely with LangChain LCEL.
    Enforces document-level RBAC, two-stage reranking, structured citations,
    and hallucination verification.
    """

    SYSTEM_PROMPT = """You are an Enterprise AI Intelligence Assistant.
Your job is to provide accurate, reliable, and strictly grounded answers to internal employees based ONLY on the verified context chunks provided below.

Strict Operational Guidelines:
1. ONLY use facts directly stated in the Context. Never extrapolate, speculate, or fabricate details.
2. If the context does not contain the answer, explicitly state: "The provided internal documents do not contain information to answer this question."
3. Every factual statement must cite its source using the exact format: [Doc: <Document Name>, Page: <Page Number>].
4. Be professional, concise, and structured (bullet points, clear headers when appropriate).

Context Chunks:
{context}

Employee Profile:
- Name: {user_name}
- Role: {user_role}
- Department: {user_dept}
- Max Security Clearance: {user_clearance}
"""

    USER_PROMPT = """Question: {query}"""

    def __init__(self):
        self.llm = self._init_llm()

    def _init_llm(self):
        """Initializes Groq LLM if API key is provided."""
        if settings.GROQ_API_KEY and "your_groq_api_key" not in settings.GROQ_API_KEY:
            try:
                from langchain_groq import ChatGroq
                logger.info(f"Initializing Groq LLM with model: {settings.GROQ_MODEL}")
                return ChatGroq(
                    model=settings.GROQ_MODEL,
                    groq_api_key=settings.GROQ_API_KEY,
                    temperature=0.1,
                    max_retries=2
                )
            except Exception as e:
                logger.warning(f"Failed to initialize ChatGroq ({e}). Will use fallback responder.")
                return None
        return None

    def _format_context(self, docs: List[Document]) -> str:
        """Formats retrieved chunks with metadata headers for the LLM prompt."""
        context_blocks = []
        for idx, doc in enumerate(docs, 1):
            m = doc.metadata
            doc_name = m.get("document_name", "Unknown")
            page = m.get("page_number", "?")
            dept = m.get("department", "General")
            clearance = m.get("access_level", "Internal")

            block = (
                f"--- [CHUNK #{idx}] ---\n"
                f"Document: {doc_name} | Page: {page} | Department: {dept} | Clearance: {clearance}\n"
                f"Content:\n{doc.page_content.strip()}"
            )
            context_blocks.append(block)

        return "\n\n".join(context_blocks)

    def _generate_fallback_response(self, query: str, docs: List[Document], user: User) -> str:
        """
        Grounded deterministic fallback responder for testing/demo environments
        when GROQ_API_KEY is not set or network is offline.
        """
        if not docs:
            return (
                f"No authorized documents found for your role ({user.role.value.capitalize()}) "
                f"and clearance level ({user.max_clearance.value.upper()}) to answer: '{query}'."
            )

        top_doc = docs[0]
        meta = top_doc.metadata
        return (
            f"Based on authorized documents ([Doc: {meta.get('document_name')}, Page: {meta.get('page_number')}]):\n\n"
            f"{top_doc.page_content.strip()[:350]}...\n\n"
            f"> [!NOTE]\n"
            f"> *Note: Operating in local demonstration mode. Add your `GROQ_API_KEY` in `.env` "
            f"to enable live generation with `{settings.GROQ_MODEL}`.*"
        )

    def answer_query(self, request: QueryRequest, user: User) -> QueryResponse:
        """Executes the complete end-to-end RAG pipeline with timing and guardrails."""
        start_time = time.perf_counter()

        # Step 1: Candidate Vector Retrieval (with document-level access control)
        retrieval_start = time.perf_counter()
        candidates_with_scores = vector_store_service.search_candidates(
            query=request.query,
            user=user,
            department_filter=request.department_filter,
            top_k=settings.TOP_K_RETRIEVAL
        )
        retrieval_time_ms = round((time.perf_counter() - retrieval_start) * 1000, 2)

        # Step 2: Two-Stage Reranking
        rerank_start = time.perf_counter()
        reranked_chunks = reranker_service.rerank(
            query=request.query,
            candidate_docs_with_scores=candidates_with_scores,
            top_n=settings.TOP_N_RERANK,
            min_relevance_score=settings.MIN_RELEVANCE_SCORE
        )
        rerank_time_ms = round((time.perf_counter() - rerank_start) * 1000, 2)

        # Step 3: LLM Generation (Pure LangChain LCEL)
        llm_start = time.perf_counter()
        if not reranked_chunks:
            answer = (
                f"Access Restriction or No Data: No authorized documents match your query '{request.query}' "
                f"under your active security clearance ({user.max_clearance.value.upper()}) "
                f"and department ({user.department.value.upper()})."
            )
            llm_time_ms = 0.0
        else:
            context_str = self._format_context(reranked_chunks)

            # Lazy-init or refresh LLM if key was added
            if self.llm is None and settings.GROQ_API_KEY:
                self.llm = self._init_llm()

            if self.llm is not None:
                try:
                    # Construct LangChain Prompt Template
                    prompt = ChatPromptTemplate.from_messages([
                        ("system", self.SYSTEM_PROMPT),
                        ("user", self.USER_PROMPT)
                    ])

                    # Build pure LangChain LCEL chain: prompt | llm | output_parser
                    chain = prompt | self.llm | StrOutputParser()

                    # Invoke LCEL chain
                    answer = chain.invoke({
                        "context": context_str,
                        "query": request.query,
                        "user_name": user.name,
                        "user_role": user.role.value.capitalize(),
                        "user_dept": user.department.value.capitalize(),
                        "user_clearance": user.max_clearance.value.upper()
                    })
                except Exception as e:
                    logger.error(f"Error during Groq LLM invocation: {e}")
                    # Try fallback model if specific model ID had issues
                    try:
                        from langchain_groq import ChatGroq
                        fallback_llm = ChatGroq(
                            model=settings.GROQ_FALLBACK_MODEL,
                            groq_api_key=settings.GROQ_API_KEY,
                            temperature=0.1
                        )
                        fallback_chain = prompt | fallback_llm | StrOutputParser()
                        answer = fallback_chain.invoke({
                            "context": context_str,
                            "query": request.query,
                            "user_name": user.name,
                            "user_role": user.role.value.capitalize(),
                            "user_dept": user.department.value.capitalize(),
                            "user_clearance": user.max_clearance.value.upper()
                        })
                    except Exception as fallback_err:
                        logger.error(f"Fallback model also failed: {fallback_err}")
                        answer = self._generate_fallback_response(request.query, reranked_chunks, user)
            else:
                answer = self._generate_fallback_response(request.query, reranked_chunks, user)

            llm_time_ms = round((time.perf_counter() - llm_start) * 1000, 2)

        total_time_ms = round((time.perf_counter() - start_time) * 1000, 2)

        # Step 4: Build Citations
        citations: List[Citation] = []
        for chunk in reranked_chunks:
            meta = chunk.metadata
            # Get short representative excerpt
            content = chunk.page_content.strip()
            excerpt = content[:160] + "..." if len(content) > 160 else content

            citations.append(Citation(
                document_name=meta.get("document_name", "Unknown Document"),
                page_number=meta.get("page_number", 1),
                department=meta.get("department", "General"),
                access_level=meta.get("access_level", "Internal"),
                relevance_score=meta.get("rerank_score", 0.85),
                excerpt=excerpt,
                chunk_id=meta.get("chunk_id", "c0")
            ))

        # Step 5: Hallucination Guardrail & Grounding Evaluation
        grounding = hallucination_service.evaluate(
            query=request.query,
            answer=answer,
            retrieved_chunks=reranked_chunks
        )

        # Step 6: Debug chunks (for inspection drawer in UI)
        debug_chunks = []
        if request.include_debug_chunks:
            for chunk in reranked_chunks:
                debug_chunks.append({
                    "chunk_id": chunk.metadata.get("chunk_id"),
                    "document_name": chunk.metadata.get("document_name"),
                    "page_number": chunk.metadata.get("page_number"),
                    "department": chunk.metadata.get("department"),
                    "access_level": chunk.metadata.get("access_level"),
                    "vector_score": chunk.metadata.get("vector_score"),
                    "rerank_score": chunk.metadata.get("rerank_score"),
                    "original_vector_rank": chunk.metadata.get("original_vector_rank"),
                    "reranked_rank": chunk.metadata.get("reranked_rank"),
                    "content": chunk.page_content
                })

        return QueryResponse(
            query=request.query,
            answer=answer,
            citations=citations,
            latency=LatencyBreakdown(
                retrieval_ms=retrieval_time_ms,
                rerank_ms=rerank_time_ms,
                llm_generation_ms=llm_time_ms,
                total_ms=total_time_ms
            ),
            grounding=grounding,
            user_context={
                "user_id": user.user_id,
                "name": user.name,
                "role": user.role.value,
                "department": user.department.value,
                "max_clearance": user.max_clearance.value,
                "allowed_clearance_levels": user.allowed_clearance_levels
            },
            chunks_retrieved_count=len(candidates_with_scores),
            chunks_used_count=len(reranked_chunks),
            debug_chunks=debug_chunks
        )

rag_chain = EnterpriseRAGChain()

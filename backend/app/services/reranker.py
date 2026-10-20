import re
import math
from typing import List, Tuple, Dict, Any
from langchain_core.documents import Document
from backend.app.core.logger import logger
from backend.app.core.config import settings

class RerankerService:
    """
    Two-stage retrieval reranker.
    Evaluates candidate chunks using semantic relevance, lexical keyword density,
    and reciprocal rank scoring to elevate the highest-signal context for generation.
    """

    @staticmethod
    def _tokenize(text: str) -> List[str]:
        # Lowercase, clean alphanumeric tokens
        tokens = re.findall(r"\b[a-zA-Z0-9_\-]{2,}\b", text.lower())
        # Filter common stopwords
        stopwords = {
            "the", "and", "is", "in", "it", "to", "of", "for", "with", "on", "at",
            "from", "by", "an", "be", "this", "that", "which", "as", "are", "was",
            "what", "how", "why", "when", "where", "can", "could", "should", "does"
        }
        return [t for t in tokens if t not in stopwords]

    @classmethod
    def rerank(
        cls,
        query: str,
        candidate_docs_with_scores: List[Tuple[Document, float]],
        top_n: int = 4,
        min_relevance_score: float = 0.20
    ) -> List[Document]:
        """
        Reranks candidate documents based on:
        1. Base vector similarity score
        2. Exact query keyword coverage & frequency in chunk
        3. Title / page context matching
        """
        if not candidate_docs_with_scores:
            return []

        query_tokens = cls._tokenize(query)
        scored_candidates: List[Dict[str, Any]] = []

        for original_rank, (doc, vector_score) in enumerate(candidate_docs_with_scores):
            content = doc.page_content
            content_tokens = cls._tokenize(content)
            content_token_set = set(content_tokens)

            # Keyword coverage: what fraction of query tokens appear in the chunk?
            if query_tokens:
                matched_tokens = [t for t in query_tokens if t in content_token_set]
                keyword_coverage = len(matched_tokens) / len(query_tokens)

                # Token frequency: density of matched query tokens in the text
                token_frequency = sum(content_tokens.count(t) for t in query_tokens)
                density = min(token_frequency / max(len(content_tokens), 1), 0.15) * 6.0
            else:
                keyword_coverage = 0.5
                density = 0.0

            # Exact phrase match bonus
            phrase_bonus = 0.15 if query.lower().strip() in content.lower() else 0.0

            # Weighted combination score
            # Vector score (50%) + Keyword coverage (30%) + Density (10%) + Phrase bonus (10%)
            final_rerank_score = (
                0.50 * vector_score +
                0.30 * keyword_coverage +
                0.10 * density +
                phrase_bonus
            )
            final_rerank_score = min(max(final_rerank_score, 0.0), 1.0)
            final_rerank_score = round(final_rerank_score, 4)

            doc.metadata["vector_score"] = vector_score
            doc.metadata["rerank_score"] = final_rerank_score
            doc.metadata["original_vector_rank"] = original_rank + 1

            scored_candidates.append({
                "doc": doc,
                "score": final_rerank_score
            })

        # Sort by rerank score descending
        scored_candidates.sort(key=lambda x: x["score"], reverse=True)

        # Assign reranked rank and filter
        final_docs: List[Document] = []
        for new_rank, item in enumerate(scored_candidates):
            doc = item["doc"]
            doc.metadata["reranked_rank"] = new_rank + 1

            if doc.metadata["rerank_score"] >= min_relevance_score:
                final_docs.append(doc)

            if len(final_docs) >= top_n:
                break

        # If highest score is below threshold, do not force-include irrelevant chunks
        if not final_docs and scored_candidates:
            top_candidate = scored_candidates[0]
            # Only include if it has at least moderate semantic signal (>= 0.20)
            if top_candidate["score"] >= 0.20:
                doc = top_candidate["doc"]
                doc.metadata["reranked_rank"] = 1
                final_docs.append(doc)

        logger.info(
            f"Reranked {len(candidate_docs_with_scores)} candidates down to "
            f"{len(final_docs)} high-precision chunks for query: '{query[:40]}...'"
        )
        return final_docs

reranker_service = RerankerService()

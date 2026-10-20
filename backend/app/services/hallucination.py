import re
from typing import List, Dict, Any, Tuple
from langchain_core.documents import Document
from backend.app.schemas.query import GroundingEvaluation
from backend.app.core.logger import logger

class HallucinationGuardrailService:
    """
    Evaluates generated RAG answers against retrieved context chunks to detect
    unsupported claims, hallucinated numbers/names, or out-of-context extrapolation.
    """

    @staticmethod
    def _extract_factual_entities(text: str) -> List[str]:
        """Extracts numerical values, percentages, currency, and capitalized terms."""
        # Numbers, dollar amounts, percentages
        numbers_and_metrics = re.findall(r"\b\$?\d+(?:\.\d+)?%?\b", text)
        # Capitalized multi-word named entities or acronyms
        named_entities = re.findall(r"\b[A-Z][a-zA-Z0-9_\-]{2,}(?:\s+[A-Z][a-zA-Z0-9_\-]{2,})*\b", text)
        return list(set(numbers_and_metrics + named_entities))

    @classmethod
    def evaluate(
        cls,
        query: str,
        answer: str,
        retrieved_chunks: List[Document]
    ) -> GroundingEvaluation:
        """
        Calculates a grounding score and hallucination risk profile based on
        lexical claim overlap and context containment.
        """
        # Case 1: Refusal / Information not found
        refusal_phrases = [
            "do not contain information",
            "does not contain information",
            "not mentioned in the provided",
            "no information found",
            "not authorized to view",
            "access denied"
        ]
        if any(phrase in answer.lower() for phrase in refusal_phrases):
            return GroundingEvaluation(
                score=100.0,
                verdict="HIGH",
                hallucination_risk="Minimal",
                supported_claims_ratio=1.0,
                reasoning="The model accurately refused to answer or stated the facts were absent from authorized context."
            )

        if not retrieved_chunks:
            return GroundingEvaluation(
                score=0.0,
                verdict="LOW",
                hallucination_risk="High",
                supported_claims_ratio=0.0,
                reasoning="No source context chunks were provided to substantiate the generated answer."
            )

        # Aggregate all retrieved text into a single context corpus
        combined_context = " ".join([chunk.page_content for chunk in retrieved_chunks]).lower()

        # Extract entities / specific claims from answer
        answer_entities = cls._extract_factual_entities(answer)

        # Exclude generic system words from entity list
        stopwords = {
            "The", "This", "That", "These", "Those", "Source", "Page", "Document",
            "According", "Furthermore", "Additionally", "Please", "However", "Note"
        }
        testable_entities = [e for e in answer_entities if e not in stopwords and len(e) > 2]

        if not testable_entities:
            # Simple answer without distinct metrics; evaluate general token overlap
            answer_tokens = set(re.findall(r"\b[a-zA-Z]{4,}\b", answer.lower()))
            if not answer_tokens:
                return GroundingEvaluation(score=100.0, verdict="HIGH", hallucination_risk="Minimal")
            overlap = [t for t in answer_tokens if t in combined_context]
            ratio = len(overlap) / len(answer_tokens)
            score = round(ratio * 100, 1)
        else:
            # Check presence of each entity in the retrieved context
            supported_count = 0
            unsupported_entities = []

            for entity in testable_entities:
                if entity.lower() in combined_context:
                    supported_count += 1
                else:
                    unsupported_entities.append(entity)

            ratio = supported_count / len(testable_entities)
            score = round(ratio * 100, 1)

        # Determine risk verdict
        if score >= 85.0:
            verdict = "HIGH"
            risk = "Minimal"
            reasoning = f"Strong context grounding: {score}% of factual claims & entities verified directly in source context."
        elif score >= 60.0:
            verdict = "MEDIUM"
            risk = "Moderate"
            reasoning = f"Moderate context grounding: {score}% of claims verified. Minor external phrasing detected."
        else:
            verdict = "LOW"
            risk = "High"
            reasoning = f"Low context grounding ({score}%). Several statements or entities could not be matched in retrieved documents."

        logger.info(f"Grounding Evaluation: Score={score}%, Verdict={verdict}, Risk={risk}")
        return GroundingEvaluation(
            score=score,
            verdict=verdict,
            hallucination_risk=risk,
            supported_claims_ratio=round(ratio, 3),
            reasoning=reasoning
        )

hallucination_service = HallucinationGuardrailService()

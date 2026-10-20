import os
import json
import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from langchain_core.documents import Document
from langchain_community.vectorstores import FAISS
from backend.app.core.config import settings
from backend.app.core.logger import logger
from backend.app.core.security import User, can_access_chunk
from backend.app.services.embeddings import EmbeddingService
from backend.app.schemas.document import DocumentRecord

class VectorStoreService:
    """
    Manages the FAISS vector index, document registry persistence,
    and metadata-enforced document access controls.
    """
    def __init__(self):
        self.index_dir = Path(settings.FAISS_INDEX_PATH)
        self.registry_file = self.index_dir / "documents_registry.json"
        self.faiss_store: Optional[FAISS] = None
        self._registry: Dict[str, Dict[str, Any]] = {}
        self._all_chunks_cache: List[Document] = []
        self._load_registry()
        self._load_vector_store()

    def _load_registry(self):
        """Loads the JSON document registry if present."""
        if self.registry_file.exists():
            try:
                with open(self.registry_file, "r", encoding="utf-8") as f:
                    self._registry = json.load(f)
            except Exception as e:
                logger.error(f"Failed to read document registry: {e}")
                self._registry = {}
        else:
            self._registry = {}

    def _save_registry(self):
        """Saves the JSON document registry to disk."""
        self.index_dir.mkdir(parents=True, exist_ok=True)
        try:
            with open(self.registry_file, "w", encoding="utf-8") as f:
                json.dump(self._registry, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save document registry: {e}")

    def _load_vector_store(self):
        """Loads FAISS index from disk if index files exist."""
        index_file = self.index_dir / "index.faiss"
        if index_file.exists():
            try:
                embeddings = EmbeddingService.get_embeddings()
                self.faiss_store = FAISS.load_local(
                    folder_path=str(self.index_dir),
                    embeddings=embeddings,
                    allow_dangerous_deserialization=True
                )
                logger.info(f"Loaded existing FAISS vector store from {self.index_dir}")
            except Exception as e:
                logger.warning(f"Could not load local FAISS index ({e}). A fresh index will be initialized.")
                self.faiss_store = None
        else:
            self.faiss_store = None

    def add_document_chunks(
        self,
        document_id: str,
        filename: str,
        chunks: List[Document],
        department: str,
        access_level: str,
        category: str,
        total_pages: int,
        file_size_bytes: int
    ) -> int:
        """Embeds and indexes document chunks in FAISS, updating registry and cache."""
        embeddings = EmbeddingService.get_embeddings()

        if self.faiss_store is None:
            self.faiss_store = FAISS.from_documents(chunks, embeddings)
        else:
            self.faiss_store.add_documents(chunks)

        # Cache in memory
        self._all_chunks_cache.extend(chunks)

        # Persist FAISS index to disk
        self.index_dir.mkdir(parents=True, exist_ok=True)
        self.faiss_store.save_local(str(self.index_dir))

        # Update document registry
        self._registry[document_id] = {
            "document_id": document_id,
            "filename": filename,
            "total_pages": total_pages,
            "total_chunks": len(chunks),
            "department": department,
            "access_level": access_level,
            "category": category,
            "file_size_bytes": file_size_bytes,
            "uploaded_at": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        self._save_registry()
        logger.info(f"Successfully indexed {len(chunks)} chunks for '{filename}' in FAISS.")
        return len(chunks)

    def search_candidates(
        self,
        query: str,
        user: User,
        department_filter: Optional[str] = None,
        top_k: int = 10
    ) -> List[Tuple[Document, float]]:
        """
        Retrieves candidate chunks using FAISS similarity search and strictly
        enforces Role-Based Document Access Controls (RBAC) and department filters.
        """
        if self.faiss_store is None:
            logger.warning("Vector store is empty. No documents indexed yet.")
            return []

        # Over-fetch candidate chunks to ensure sufficient candidates after access filtering
        fetch_k = max(top_k * 4, 25)
        raw_results = self.faiss_store.similarity_search_with_score(query, k=fetch_k)

        authorized_candidates: List[Tuple[Document, float]] = []

        for doc, score in raw_results:
            # 1. Enforce Document-Level RBAC
            if not can_access_chunk(user, doc.metadata):
                continue

            # 2. Enforce explicit department query filter if selected by user
            if department_filter and department_filter.lower() not in ["all", ""]:
                doc_dept = doc.metadata.get("department", "").lower()
                if doc_dept != department_filter.lower() and doc_dept not in ["all", "general"]:
                    continue

            # Convert FAISS L2 distance or cosine distance to normalized similarity score (0 to 1)
            # In FAISS L2 distance: lower score means closer distance. Normalized similarity: 1 / (1 + score)
            normalized_score = round(1.0 / (1.0 + float(score)), 4)
            doc.metadata["vector_similarity_score"] = normalized_score
            authorized_candidates.append((doc, normalized_score))

            if len(authorized_candidates) >= top_k:
                break

        return authorized_candidates

    def list_documents(self) -> List[DocumentRecord]:
        """Returns all documents registered in the system."""
        docs = []
        for doc_data in self._registry.values():
            docs.append(DocumentRecord(**doc_data))
        return sorted(docs, key=lambda x: x.uploaded_at, reverse=True)

    def get_document_chunks(self, document_id: str) -> List[Dict[str, Any]]:
        """Inspects all chunks for a given document."""
        chunks_info = []
        # If cache is populated, look there, otherwise search docstore
        if self.faiss_store and hasattr(self.faiss_store, "docstore"):
            for doc in self.faiss_store.docstore._dict.values():
                if doc.metadata.get("document_id") == document_id:
                    chunks_info.append({
                        "chunk_id": doc.metadata.get("chunk_id"),
                        "page_number": doc.metadata.get("page_number"),
                        "content": doc.page_content,
                        "department": doc.metadata.get("department"),
                        "access_level": doc.metadata.get("access_level"),
                    })
        return sorted(chunks_info, key=lambda x: x.get("page_number", 0))

    def delete_document(self, document_id: str) -> bool:
        """Deletes a document from the registry and rebuilds FAISS index without its chunks."""
        if document_id not in self._registry:
            return False

        del self._registry[document_id]
        self._save_registry()

        # Rebuild FAISS index from remaining documents in docstore
        if self.faiss_store and hasattr(self.faiss_store, "docstore"):
            remaining_docs = [
                doc for doc in self.faiss_store.docstore._dict.values()
                if doc.metadata.get("document_id") != document_id
            ]

            if remaining_docs:
                embeddings = EmbeddingService.get_embeddings()
                self.faiss_store = FAISS.from_documents(remaining_docs, embeddings)
                self.faiss_store.save_local(str(self.index_dir))
            else:
                self.faiss_store = None
                # Clear index files
                for f in ["index.faiss", "index.pkl"]:
                    p = self.index_dir / f
                    if p.exists():
                        p.unlink()

        logger.info(f"Deleted document {document_id} and refreshed FAISS index.")
        return True

    def get_stats(self) -> Dict[str, Any]:
        """Returns enterprise vector store statistics."""
        total_docs = len(self._registry)
        total_chunks = sum(d.get("total_chunks", 0) for d in self._registry.values())
        departments = {}
        access_levels = {}

        for d in self._registry.values():
            dept = d.get("department", "general")
            departments[dept] = departments.get(dept, 0) + 1

            level = d.get("access_level", "internal")
            access_levels[level] = access_levels.get(level, 0) + 1

        return {
            "total_documents": total_docs,
            "total_chunks": total_chunks,
            "departments": departments,
            "access_levels": access_levels,
            "embedding_provider": EmbeddingService.get_provider_info()
        }

# Global singleton
vector_store_service = VectorStoreService()

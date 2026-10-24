"""
AgentMail AI - Context Retriever
Queries vector store and formats retrieved chunks for agent prompt injection.
"""

from typing import List, Dict, Any
from backend.rag.vector_store import LocalVectorStore


class RAGRetriever:
    def __init__(self, vector_store: LocalVectorStore = None):
        self.store = vector_store or LocalVectorStore()

    def retrieve_context(self, query: str, top_k: int = 3) -> Dict[str, Any]:
        """
        Retrieves top_k context chunks relevant to the email query.
        Returns both raw chunk objects and a concatenated string for prompt injection.
        """
        chunks = self.store.similarity_search(query, top_k=top_k)
        if not chunks:
            return {
                "chunks": [],
                "formatted_text": "No specific context found in knowledge base.",
                "sources": []
            }

        formatted_pieces = []
        sources = []
        for i, chunk in enumerate(chunks, 1):
            source_tag = f"[{chunk['category']}] ({chunk['source_file']}, score: {chunk['score']})"
            formatted_pieces.append(f"--- Document Source {i}: {source_tag} ---\n{chunk['content']}")
            sources.append(chunk["source_file"])

        formatted_text = "\n\n".join(formatted_pieces)
        return {
            "chunks": chunks,
            "formatted_text": formatted_text,
            "sources": list(set(sources))
        }

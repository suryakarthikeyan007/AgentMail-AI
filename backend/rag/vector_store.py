"""
AgentMail AI - Local Vector Store & RAG Engine
Implements document ingestion, text chunking, nomic-embed-text embeddings via Ollama,
persistent local vector storage, and cosine-similarity retrieval.
"""

import os
import json
import logging
import sqlite3
from pathlib import Path
from typing import List, Dict, Any, Optional
import httpx
import numpy as np

from backend.config import OLLAMA_BASE_URL, EMBEDDING_MODEL, KNOWLEDGE_BASE_DIR, DATABASE_PATH, LLM_TIMEOUT

logger = logging.getLogger("agentmail.rag")


class LocalVectorStore:
    def __init__(self, db_path: Path = DATABASE_PATH, kb_dir: Path = KNOWLEDGE_BASE_DIR):
        self.db_path = db_path
        self.kb_dir = kb_dir
        self.ollama_url = f"{OLLAMA_BASE_URL}/api/embeddings"
        self._init_vector_table()

    def _init_vector_table(self):
        """Creates the SQLite table for vector chunks and embeddings."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS rag_chunks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_file TEXT,
                category TEXT,
                content TEXT,
                embedding_json TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        conn.close()

    def get_embedding(self, text: str) -> Optional[List[float]]:
        """Generates a 768-dim embedding vector using nomic-embed-text via Ollama."""
        text_clean = text.strip().replace("\r\n", "\n")
        if not text_clean:
            return None
        try:
            with httpx.Client(timeout=LLM_TIMEOUT) as client:
                res = client.post(
                    self.ollama_url,
                    json={"model": EMBEDDING_MODEL, "prompt": text_clean}
                )
                if res.status_code == 200:
                    data = res.json()
                    return data.get("embedding", [])
                else:
                    logger.error(f"Ollama embedding error: {res.status_code} - {res.text}")
        except Exception as e:
            logger.error(f"Failed to fetch embedding: {str(e)}")
        return None

    def chunk_markdown(self, text: str, max_chunk_words: int = 150) -> List[str]:
        """Splits markdown content into cohesive paragraphs or section chunks."""
        sections = text.split("\n\n")
        chunks = []
        current_chunk = []
        current_word_count = 0

        for section in sections:
            sec = section.strip()
            if not sec:
                continue
            words = sec.split()
            sec_word_count = len(words)

            if current_word_count + sec_word_count > max_chunk_words and current_chunk:
                chunks.append("\n\n".join(current_chunk))
                current_chunk = [sec]
                current_word_count = sec_word_count
            else:
                current_chunk.append(sec)
                current_word_count += sec_word_count

        if current_chunk:
            chunks.append("\n\n".join(current_chunk))

        return chunks

    def index_knowledge_base(self, force_reindex: bool = False) -> int:
        """Reads all documents in knowledge_base/, computes embeddings, and persists them."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        if force_reindex:
            cursor.execute("DELETE FROM rag_chunks")
            conn.commit()
        else:
            cursor.execute("SELECT COUNT(*) FROM rag_chunks")
            count = cursor.fetchone()[0]
            if count > 0:
                logger.info(f"RAG vector store already contains {count} indexed chunks.")
                conn.close()
                return count

        indexed_count = 0
        if not self.kb_dir.exists():
            logger.warning(f"Knowledge base directory {self.kb_dir} does not exist.")
            conn.close()
            return 0

        for filepath in self.kb_dir.rglob("*.md"):
            try:
                content = filepath.read_text(encoding="utf-8")
                category = filepath.parent.name
                source_rel = str(filepath.relative_to(self.kb_dir.parent))
                chunks = self.chunk_markdown(content)

                for chunk in chunks:
                    emb = self.get_embedding(chunk)
                    if emb:
                        cursor.execute("""
                            INSERT INTO rag_chunks (source_file, category, content, embedding_json)
                            VALUES (?, ?, ?, ?)
                        """, (source_rel, category, chunk, json.dumps(emb)))
                        indexed_count += 1
            except Exception as e:
                logger.error(f"Error indexing {filepath}: {str(e)}")

        conn.commit()
        conn.close()
        logger.info(f"Successfully indexed {indexed_count} knowledge chunks into local RAG store.")
        return indexed_count

    def similarity_search(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """Performs cosine-similarity search against stored chunks."""
        query_emb = self.get_embedding(query)
        if not query_emb:
            return []

        q_vec = np.array(query_emb, dtype=np.float32)
        q_norm = np.linalg.norm(q_vec)
        if q_norm == 0:
            return []

        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT id, source_file, category, content, embedding_json FROM rag_chunks")
        rows = cursor.fetchall()
        conn.close()

        results = []
        for row in rows:
            try:
                emb_list = json.loads(row["embedding_json"])
                doc_vec = np.array(emb_list, dtype=np.float32)
                doc_norm = np.linalg.norm(doc_vec)
                if doc_norm > 0:
                    cosine_sim = float(np.dot(q_vec, doc_vec) / (q_norm * doc_norm))
                    results.append({
                        "id": row["id"],
                        "source_file": row["source_file"],
                        "category": row["category"],
                        "content": row["content"],
                        "score": round(cosine_sim, 4)
                    })
            except Exception:
                continue

        # Sort descending by cosine similarity score
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]

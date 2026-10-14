import json
import logging
import pickle
import re
from pathlib import Path
from typing import List, Dict, Any, Tuple
import numpy as np
import httpx

try:
    import faiss
    HAS_FAISS = True
except ImportError:
    HAS_FAISS = False

from app.config import settings

logger = logging.getLogger("sales_ops.rag")

STOP_WORDS = {
    "the", "and", "for", "are", "but", "not", "you", "all", "any", "can", "had",
    "her", "was", "one", "our", "out", "day", "get", "has", "him", "his", "how",
    "man", "new", "now", "old", "see", "two", "way", "who", "boy", "did", "its",
    "let", "put", "say", "she", "too", "use", "what", "where", "which", "with",
    "about", "would", "there", "their", "please", "tell", "show", "give", "much",
    "many", "some"
}


def tokenize(text: str) -> List[str]:
    return [w for w in re.sub(r"[^a-zA-Z0-9\s]", " ", text.lower()).split() if len(w) > 2]


class RAGService:
    def __init__(self):
        self.index_path = Path("faiss_index.index")
        self.metadata_path = Path("faiss_index_metadata.pkl")
        self.chunks_path = Path("app/data/knowledge_base.json")
        self.chunks: List[Dict[str, Any]] = []
        self.vectorizer = None
        self.faiss_index = None

        self._load_faiss_and_chunks()

    def _load_faiss_and_chunks(self):
        # 1. Try loading FAISS index and metadata
        if HAS_FAISS and self.index_path.exists() and self.metadata_path.exists():
            try:
                self.faiss_index = faiss.read_index(str(self.index_path))
                with open(self.metadata_path, "rb") as f:
                    meta = pickle.load(f)
                self.vectorizer = meta.get("vectorizer")
                self.chunks = meta.get("chunks", [])
                logger.info(f"Loaded FAISS index ({self.faiss_index.ntotal} vectors) and {len(self.chunks)} chunks.")
                return
            except Exception as e:
                logger.error(f"Error loading FAISS index: {e}. Falling back to JSON chunks.")

        # 2. Fallback to direct JSON knowledge chunks
        if self.chunks_path.exists():
            try:
                with open(self.chunks_path, "r", encoding="utf-8") as f:
                    self.chunks = json.load(f)
                logger.info(f"Loaded {len(self.chunks)} verified knowledge chunks from JSON.")
            except Exception as e:
                logger.error(f"Error loading knowledge base: {e}")
                self.chunks = []

    def retrieve(self, query: str, top_k: int = 4) -> List[Dict[str, Any]]:
        # If FAISS is loaded, use FAISS cosine similarity search
        if self.faiss_index is not None and self.vectorizer is not None and len(self.chunks) > 0:
            try:
                q_vec = self.vectorizer.transform([query]).toarray().astype(np.float32)
                faiss.normalize_L2(q_vec)
                k = min(top_k, self.faiss_index.ntotal)
                distances, indices = self.faiss_index.search(q_vec, k)

                retrieved = []
                for idx, dist in zip(indices[0], distances[0]):
                    if idx >= 0 and idx < len(self.chunks):
                        retrieved.append(self.chunks[idx])
                if retrieved:
                    return retrieved
            except Exception as e:
                logger.error(f"FAISS search failed: {e}. Falling back to lexical search.")

        # Fallback lexical and keyword search
        tokens = [t for t in tokenize(query) if t not in STOP_WORDS]
        query_lower = query.lower()

        scored = []
        for chunk in self.chunks:
            score = 0
            content_lower = chunk.get("content", "").lower()
            title_lower = chunk.get("title", "").lower()
            category_lower = chunk.get("category", "").lower()
            chunk_tokens = tokenize(chunk.get("content", ""))

            if len(tokens) > 1 and query_lower in content_lower:
                score += 25
            if query_lower in title_lower:
                score += 35

            for token in tokens:
                for kw in chunk.get("keywords", []):
                    if token in kw.lower():
                        score += 8
                if token in title_lower:
                    score += 6
                if token in category_lower:
                    score += 4

                count = chunk_tokens.count(token)
                if count > 0:
                    score += min(count * 1.5, 9)

                if token.isdigit() and token in content_lower:
                    score += 15

            if score > 2:
                scored.append({"chunk": chunk, "score": score})

        scored.sort(key=lambda x: x["score"], reverse=True)
        return [item["chunk"] for item in scored[:top_k]]

    def query(self, user_query: str) -> Dict[str, Any]:
        """Query RAG with FAISS retrieval and Groq LLM inference."""
        relevant_chunks = self.retrieve(user_query, top_k=4)

        sources = [
            {
                "id": c.get("id"),
                "title": c.get("title"),
                "file": c.get("source_file"),
                "sheet": c.get("source_sheet"),
                "category": c.get("category")
            }
            for c in relevant_chunks
        ]

        if not relevant_chunks:
            return {
                "answer": "I do not have verified records regarding this question in the official Sunset Kuakata sales operations ledgers.",
                "sources": [],
                "model": "Fallback"
            }

        context_str = "\n\n---\n\n".join([
            f"### [Source {i+1}] {c['title']}\n"
            f"File: {c['source_file']} | Sheet: {c['source_sheet']} | Category: {c['category']}\n"
            f"{c['content']}"
            for i, c in enumerate(relevant_chunks)
        ])

        system_prompt = (
            "You are the executive AI Sales Operations & Investment Advisor for Sunset Kuakata Hotel & Resort Ltd. "
            "Your role is to provide precise, grounded answers regarding hotel share pricing, discounts, executive sales quotas, "
            "revenue collections, property amenities, and investor rights based on actual corporate records.\n\n"
            "RULES:\n"
            "1. Answer ONLY using the facts present in the EXCERPTS provided below.\n"
            "2. Whenever citing a figure, price, executive ranking, or policy, append the source in brackets, e.g. [Source: Discount Price.xlsx / Sheet1].\n"
            "3. If the user's question asks for information not present in the excerpts, state clearly: "
            "'I cannot find this information in the official Sunset Kuakata sales records.'\n"
            "4. Format clearly with bullet points, structured tables, or bold numbers where appropriate.\n"
            "5. All amounts are in Bangladeshi Taka (BDT).\n\n"
            f"OFFICIAL VERIFIED EXCERPTS:\n{context_str}"
        )

        api_key = settings.GROQ_API_KEY
        model = settings.GROQ_MODEL if settings.GROQ_MODEL != "llama-3.3-70b-versatile" else "openai/gpt-oss-120b"

        if api_key:
            try:
                headers = {
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                }
                payload = {
                    "model": model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_query}
                    ],
                    "temperature": 0.2
                }
                with httpx.Client(timeout=30.0) as client:
                    resp = client.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload)
                    if resp.status_code == 200:
                        data = resp.json()
                        answer = data["choices"][0]["message"]["content"]
                        return {
                            "answer": answer,
                            "sources": sources,
                            "model": model,
                            "retriever": "FAISS (Vector Index)" if self.faiss_index else "Lexical Index"
                        }
                    else:
                        logger.warning(f"Groq API returned HTTP {resp.status_code}: {resp.text}")
            except Exception as e:
                logger.error(f"Error querying Groq API: {e}")

        # Deterministic fallback when API key is missing or unreachable
        primary = relevant_chunks[0]
        answer = (
            f"**Information from {primary['title']}**\n\n"
            f"{primary['content']}\n\n"
            f"*Source: [{primary['source_file']} / {primary['source_sheet']}]*"
        )
        return {
            "answer": answer,
            "sources": sources,
            "model": "Deterministic Ledger Fallback",
            "retriever": "FAISS (Vector Index)" if self.faiss_index else "Lexical Index"
        }


rag_service = RAGService()

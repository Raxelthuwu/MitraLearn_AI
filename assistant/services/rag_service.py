import os
from typing import Any, Dict, List, Optional, Tuple
from django.conf import settings
from assistant.Assistant_vector_models import ChatEmbedding
from core.ai_manager import AIManager

class RAGService:
    """
    RAG (Retrieval-Augmented Generation) Service.
    Orchestrates the retrieval of documents from ChromaDB and 
    generates responses with academic references.
    """

    def __init__(self):
        self.embedding_service = AIManager.get_embedding_service()
        self.llm_service = AIManager.get_llm_service()
        self.min_similarity = getattr(settings, "CHAT_RAG_MIN_SIMILARITY", 0.55)

    @staticmethod
    def _distance_to_similarity(distance: float) -> float:
        return round(max(0.0, 1.0 - (float(distance) / 2.0)), 4)

    @staticmethod
    def _parse_chroma_results(results: dict) -> List[Dict[str, Any]]:
        if not results:
            return []
        ids = results.get("ids", [[]])[0]
        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]

        parsed = []
        for i, chunk_id in enumerate(ids):
            parsed.append({
                "chunkId": chunk_id,
                "document": documents[i] if i < len(documents) else "",
                "metadata": metadatas[i] if i < len(metadatas) else {},
                "distance": distances[i] if i < len(distances) else 1.0,
            })
        return parsed

    def retrieve_context(
        self,
        query: str,
        subcategory_id: Optional[str] = None,
        topic_id: Optional[str] = None,
        k: int = 3,
    ) -> Tuple[str, List[Dict[str, Any]], bool]:
        """
        Returns (context_text, source_fragments, context_sufficient).
        """
        embedding = self.embedding_service.embed(query)
        raw = ChatEmbedding.search(
            embedding,
            n_results=k,
            subcategory_id=subcategory_id,
            topic_id=topic_id,
        )
        fragments = self._parse_chroma_results(raw)

        # Fallback: if no fragments match the subcategory/topic filters, search globally
        if not fragments and (subcategory_id or topic_id):
            raw = ChatEmbedding.search(
                embedding,
                n_results=k,
            )
            fragments = self._parse_chroma_results(raw)

        if not fragments:
            return "", [], False

        best_similarity = self._distance_to_similarity(fragments[0]["distance"])
        sufficient = best_similarity >= self.min_similarity

        sources = []
        context_parts = []
        for frag in fragments:
            sim = self._distance_to_similarity(frag["distance"])
            if sim < self.min_similarity:
                continue
            meta = frag["metadata"]
            source = meta.get("source", "Material")
            source_basename = os.path.basename(source)
            sources.append({
                "source": source_basename,
                "page": meta.get("page", 0),
                "similarity": sim,
                "snippet": frag["document"][:300],
            })
            page = meta.get("page", "?")
            context_parts.append(f"[{source_basename}, pág. {page}]\n{frag['document']}")

        context = "\n\n---\n\n".join(context_parts)
        return context, sources, sufficient and bool(context_parts)

    def _format_sources_label(self, sources: List[Dict[str, Any]]) -> str:
        if not sources:
            return "Sin fuentes indexadas"
        labels = []
        for s in sources:
            labels.append(f"{s['source']} (pág. {s['page']})")
        return ", ".join(labels)

    def generate_augmented_response(
        self,
        query: str,
        subcategory_id: Optional[str] = None,
        topic_id: Optional[str] = None,
        program_objectives: str = "",
    ) -> Dict[str, Any]:
        context, sources, sufficient = self.retrieve_context(
            query, subcategory_id, topic_id, k=4
        )

        if not sufficient:
            return {
                "answer": "",
                "sources": "",
                "sourceFragments": sources,
                "contextInsufficient": True,
            }

        objectives_block = ""
        if program_objectives:
            objectives_block = f"\nObjetivos del programa:\n{program_objectives}\n"

        prompt = f"""Eres un asistente académico de Ingeniería de Sistemas (Universidad de Pamplona).
Responde en español usando SOLO el contexto proporcionado. Si el contexto no alcanza, dilo claramente.
Cita el material cuando sea posible (libro y página).
{objectives_block}
Contexto:
{context}

Pregunta del estudiante: {query}

Respuesta:"""

        answer = self.llm_service.generate_response(prompt)
        return {
            "answer": answer,
            "sources": self._format_sources_label(sources),
            "sourceFragments": sources,
            "contextInsufficient": False,
        }

    # Backward-compatible helper used by forum Academic posts
    def generate_augmented_response_simple(self, query: str) -> Dict[str, Any]:
        res = self.generate_augmented_response(query)
        if res.get("contextInsufficient"):
            # Return a default message if context is insufficient
            return {
                "answer": "Lo siento, no encuentro información suficiente en los materiales cargados para responder a tu pregunta.",
                "sources": "Sin fuentes indexadas"
            }
        return res

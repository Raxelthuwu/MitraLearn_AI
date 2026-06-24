import re
from collections import Counter
from string import Template
from typing import Any, Dict, List, Optional

from forum.interfaces import (
    ISemanticIndexService,
    ISemanticSearchService,
    IDuplicateDetectionService,
    IAnswerSuggestionService,
    IQueryExpansionService,
)

from forum.models import ForumPost, ForumReply
from forum.ForumVectorModels import ForumEmbedding
from core.ai_manager import AIManager


class ForumSemanticHelpers:

    @staticmethod
    def embedIdForPost(postId: str) -> str:
        # Canonical vector store ID for a post
        return f"post_{postId}"

    @staticmethod
    def embedIdForReply(replyId: str) -> str:
        # Canonical vector store ID for a reply
        return f"reply_{replyId}"

    @staticmethod
    def buildPostText(title: str, content: str, tags: List[str]) -> str:
        # Joins post fields into a single embeddable string
        tagsStr = " ".join(tags) if tags else ""
        return f"{title}\n\n{content}\n\nTags: {tagsStr}".strip()

    @staticmethod
    def parseChromaResults(results: dict) -> List[Dict[str, Any]]:
        # Flattens ChromaDB nested-list response into a plain list of dicts
        ids       = results.get("ids", [[]])[0]
        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]

        parsed = []
        for i, embedId in enumerate(ids):
            parsed.append({
                "embedId":  embedId,
                "document": documents[i] if i < len(documents) else "",
                "metadata": metadatas[i] if i < len(metadatas) else {},
                "distance": distances[i] if i < len(distances) else 1.0,
            })

        return parsed

    @staticmethod
    def distanceToSimilarity(distance: float) -> float:
        # Converts ChromaDB cosine distance [0, 2] to similarity score [0, 1]
        return round(max(0.0, 1.0 - (distance / 2.0)), 4)


# SemanticIndexService
class SemanticIndexService(ISemanticIndexService):

    def indexPost(self, postId: str, title: str, content: str, tags: List[str]) -> bool:
        # Embeds post text and stores it in ChromaDB as type "question"
        try:
            embeddingSvc = AIManager.get_embedding_service()
            documentText = ForumSemanticHelpers.buildPostText(title, content, tags)
            embedding    = embeddingSvc.embed(documentText)
            embedId      = ForumSemanticHelpers.embedIdForPost(postId)

            print(f"[DEBUG] SemanticIndexService.indexPost -> postId: {postId}, embedId: {embedId}")

            ForumEmbedding.add(
                embed_id      = embedId,
                embedding     = embedding,
                document_text = documentText,
                post_id       = postId,
                type_         = "question",
                topic         = "",
                category      = "General",
                score         = 0.0,
                is_accepted   = False,
            )

            print(f"[DEBUG] SemanticIndexService.indexPost -> indexed successfully")
            return True

        except Exception as e:
            print(f"[ERROR] SemanticIndexService.indexPost -> {e}")
            return False

    def updateIndexedPost(self, postId: str, title: str, content: str, tags: List[str]) -> bool:
        # ChromaDB has no in-place update; delete then re-add
        self.removeIndexedPost(postId)
        return self.indexPost(postId, title, content, tags)

    def removeIndexedPost(self, postId: str) -> bool:
        # Deletes the post vector from the store
        try:
            embedId = ForumSemanticHelpers.embedIdForPost(postId)
            ForumEmbedding.delete(embedId)
            print(f"[DEBUG] SemanticIndexService.removeIndexedPost -> removed {embedId}")
            return True
        except Exception as e:
            print(f"[ERROR] SemanticIndexService.removeIndexedPost -> {e}")
            return False

    def indexReply(self, replyId: str, postId: str, content: str) -> bool:
        # Embeds reply content and stores it in ChromaDB as type "answer"
        try:
            embeddingSvc = AIManager.get_embedding_service()
            embedding    = embeddingSvc.embed(content)
            embedId      = ForumSemanticHelpers.embedIdForReply(replyId)

            print(f"[DEBUG] SemanticIndexService.indexReply -> replyId: {replyId}, embedId: {embedId}")

            ForumEmbedding.add(
                embed_id      = embedId,
                embedding     = embedding,
                document_text = content,
                post_id       = postId,
                type_         = "answer",
                topic         = "",
                category      = "General",
                reply_id      = replyId,
                score         = 0.0,
                is_accepted   = False,
            )

            print(f"[DEBUG] SemanticIndexService.indexReply -> indexed successfully")
            return True

        except Exception as e:
            print(f"[ERROR] SemanticIndexService.indexReply -> {e}")
            return False

    def removeIndexedReply(self, replyId: str) -> bool:
        # Deletes the reply vector from the store
        try:
            embedId = ForumSemanticHelpers.embedIdForReply(replyId)
            ForumEmbedding.delete(embedId)
            print(f"[DEBUG] SemanticIndexService.removeIndexedReply -> removed {embedId}")
            return True
        except Exception as e:
            print(f"[ERROR] SemanticIndexService.removeIndexedReply -> {e}")
            return False

    def rebuildIndex(self) -> int:
        # Drops all existing embeddings and rebuilds from MongoDB; returns count indexed
        print("[DEBUG] SemanticIndexService.rebuildIndex -> starting full rebuild")

        # Remove all existing forum embeddings before rebuilding
        try:
            existing = ForumEmbedding.collection.get()
            existingIds = existing.get("ids", [])
            if existingIds:
                ForumEmbedding.collection.delete(ids=existingIds)
                print(f"[DEBUG] SemanticIndexService.rebuildIndex -> deleted {len(existingIds)} existing embeddings")
        except Exception as e:
            print(f"[ERROR] SemanticIndexService.rebuildIndex -> failed to clear index: {e}")

        indexed = 0

        # Re-index every post as a question
        for post in ForumPost.get_all():
            postId  = str(post["_id"])
            title   = post.get("title", "")
            content = post.get("content", "")
            tags    = post.get("tags", [])

            if self.indexPost(postId, title, content, tags):
                indexed += 1

        # Re-index every reply as an answer
        for reply in ForumReply.get_all():
            replyId = str(reply["_id"])
            postId  = str(reply["postId"])
            content = reply.get("content", "")

            if self.indexReply(replyId, postId, content):
                indexed += 1

        print(f"[DEBUG] SemanticIndexService.rebuildIndex -> total indexed: {indexed}")
        return indexed


# SemanticSearchService
class SemanticSearchService(ISemanticSearchService):

    # Minimum cosine similarity for user-facing search results
    DEFAULT_SEARCH_THRESHOLD: float = 0.72
    # Drop results far below the best match (reduces noise in small corpora)
    SEARCH_RELATIVE_GAP: float = 0.08

    def findSimilarPosts(
        self,
        queryText: str,
        topK: int,
        scoreThreshold: float,
    ) -> List[Dict[str, Any]]:
        # Returns top-K posts whose similarity exceeds scoreThreshold
        embeddingSvc = AIManager.get_embedding_service()
        embedding    = embeddingSvc.embed(queryText)

        print(f"[DEBUG] SemanticSearchService.findSimilarPosts -> topK: {topK}, threshold: {scoreThreshold}")

        raw     = ForumEmbedding.search_duplicates(embedding, n_results=topK)
        results = ForumSemanticHelpers.parseChromaResults(raw)

        output = []
        for item in results:
            similarity = ForumSemanticHelpers.distanceToSimilarity(item["distance"])
            if similarity < scoreThreshold:
                continue

            meta = item["metadata"]
            output.append({
                "postId":     meta.get("postId", ""),
                "snippet":    item["document"][:300],
                "similarity": similarity,
                "topic":      meta.get("topic", ""),
                "category":   meta.get("category", ""),
                "score":      meta.get("score", 0.0),
                "status":     meta.get("status", "open"),
            })

        if output:
            output.sort(key=lambda r: r["similarity"], reverse=True)
            top_similarity = output[0]["similarity"]
            relative_floor = top_similarity - self.SEARCH_RELATIVE_GAP
            effective_min  = max(scoreThreshold, relative_floor)
            output = [r for r in output if r["similarity"] >= effective_min]
            print(
                f"[DEBUG] SemanticSearchService.findSimilarPosts -> "
                f"{len(output)} results after relative filter (top={top_similarity}, min={effective_min})"
            )
        else:
            print(f"[DEBUG] SemanticSearchService.findSimilarPosts -> 0 results above threshold")

        return output

    def findSimilarPostById(
        self,
        postId: str,
        topK: int,
        scoreThreshold: float,
    ) -> List[Dict[str, Any]]:
        # Fetches the post from MongoDB and delegates to findSimilarPosts
        post = ForumPost.get_by_id(postId)
        if not post:
            print(f"[DEBUG] SemanticSearchService.findSimilarPostById -> post {postId} not found")
            return []

        combined = ForumSemanticHelpers.buildPostText(
            post.get("title", ""),
            post.get("content", ""),
            post.get("tags", []),
        )
        return self.findSimilarPosts(combined, topK, scoreThreshold)

    def findRelevantReplies(
        self,
        queryText: str,
        topK: int,
        scoreThreshold: float,
    ) -> List[Dict[str, Any]]:
        # Returns replies semantically close to the query; accepted answers get +0.05 bonus
        embeddingSvc = AIManager.get_embedding_service()
        embedding    = embeddingSvc.embed(queryText)

        print(f"[DEBUG] SemanticSearchService.findRelevantReplies -> topK: {topK}")

        raw     = ForumEmbedding.search_answers(embedding, n_results=topK * 2)
        results = ForumSemanticHelpers.parseChromaResults(raw)

        output = []
        for item in results:
            meta = item["metadata"]

            similarity = ForumSemanticHelpers.distanceToSimilarity(item["distance"])

            # Accepted answers surface above equally-scored candidates
            if meta.get("isAccepted"):
                similarity = min(1.0, similarity + 0.05)

            if similarity < scoreThreshold:
                continue

            output.append({
                "replyId":    meta.get("replyId", ""),
                "postId":     meta.get("postId", ""),
                "snippet":    item["document"][:300],
                "similarity": similarity,
                "isAccepted": meta.get("isAccepted", False),
                "score":      meta.get("score", 0.0),
            })

        output.sort(key=lambda x: x["similarity"], reverse=True)
        print(f"[DEBUG] SemanticSearchService.findRelevantReplies -> {len(output[:topK])} results")
        return output[:topK]

    def searchByTags(
        self,
        tags: List[str],
        queryText: Optional[str],
        topK: int,
    ) -> List[Dict[str, Any]]:
        # Embeds tags + optional query, then filters results by topic metadata overlap
        embeddingSvc = AIManager.get_embedding_service()
        query        = queryText or " ".join(tags)
        embedding    = embeddingSvc.embed(query)

        print(f"[DEBUG] SemanticSearchService.searchByTags -> tags: {tags}, topK: {topK}")

        raw       = ForumEmbedding.search(embedding, n_results=topK * 3)
        results   = ForumSemanticHelpers.parseChromaResults(raw)
        tagsLower = [t.lower() for t in tags]

        output = []
        for item in results:
            meta  = item["metadata"]
            topic = meta.get("topic", "").lower()

            # Skip items with no tag overlap in their topic field
            if not any(tag in topic for tag in tagsLower):
                continue

            output.append({
                "postId":     meta.get("postId", ""),
                "snippet":    item["document"][:300],
                "similarity": ForumSemanticHelpers.distanceToSimilarity(item["distance"]),
                "topic":      meta.get("topic", ""),
                "category":   meta.get("category", ""),
            })

        output.sort(key=lambda x: x["similarity"], reverse=True)
        print(f"[DEBUG] SemanticSearchService.searchByTags -> {len(output[:topK])} results")
        return output[:topK]


# DuplicateDetectionService
class DuplicateDetectionService(IDuplicateDetectionService):

    # Threshold for soft duplicate warnings shown to the user
    SOFT_THRESHOLD: float = 0.88
    # Threshold for hard blocks before submission
    HARD_THRESHOLD: float = 0.95

    def detectDuplicates(
        self,
        title: str,
        content: str,
        scoreThreshold: float,
    ) -> List[Dict[str, Any]]:
        # Returns candidate posts whose similarity exceeds scoreThreshold
        embeddingSvc = AIManager.get_embedding_service()
        documentText = ForumSemanticHelpers.buildPostText(title, content, [])
        embedding    = embeddingSvc.embed(documentText)

        print(f"[DEBUG] DuplicateDetectionService.detectDuplicates -> threshold: {scoreThreshold}")

        raw     = ForumEmbedding.search_duplicates(embedding, n_results=10)
        results = ForumSemanticHelpers.parseChromaResults(raw)

        candidates = []
        for item in results:
            similarity = ForumSemanticHelpers.distanceToSimilarity(item["distance"])
            if similarity < scoreThreshold:
                continue

            meta = item["metadata"]
            candidates.append({
                "postId":     meta.get("postId", ""),
                "snippet":    item["document"][:300],
                "similarity": similarity,
                "status":     meta.get("status", "open"),
                "score":      meta.get("score", 0.0),
                "topic":      meta.get("topic", ""),
            })

        candidates.sort(key=lambda x: x["similarity"], reverse=True)
        print(f"[DEBUG] DuplicateDetectionService.detectDuplicates -> {len(candidates)} candidates")
        return candidates

    def isClearDuplicate(self, title: str, content: str, hardThreshold: float) -> bool:
        # Fast pre-check; True means the post should be blocked or strongly warned
        candidates = self.detectDuplicates(title, content, hardThreshold)
        isDup = len(candidates) > 0

        print(f"[DEBUG] DuplicateDetectionService.isClearDuplicate -> {isDup} (threshold: {hardThreshold})")
        return isDup

    def confirmDuplicate(self, postId: str, originalPostId: str) -> Dict[str, Any]:
        # Links the post to its original in MongoDB and removes its embedding
        print(f"[DEBUG] DuplicateDetectionService.confirmDuplicate -> {postId} -> {originalPostId}")

        ForumPost.mark_as_duplicate(postId, originalPostId)

        # Remove duplicate embedding to keep the index clean
        SemanticIndexService().removeIndexedPost(postId)

        updated = ForumPost.get_by_id(postId)
        if not updated:
            return {}

        return {
            "postId":         postId,
            "duplicatedFrom": originalPostId,
            "status":         updated.get("status", "closed"),
        }

    def getDuplicatesOfPost(self, originalPostId: str) -> List[Dict[str, Any]]:
        # Queries MongoDB for all posts confirmed as duplicates of originalPostId
        from bson import ObjectId

        print(f"[DEBUG] DuplicateDetectionService.getDuplicatesOfPost -> {originalPostId}")

        duplicates = list(
            ForumPost.collection.find({"duplicatedFrom": ObjectId(originalPostId)})
        )

        return [
            {
                "postId":    str(d["_id"]),
                "title":     d.get("title", ""),
                "status":    d.get("status", "closed"),
                "createdAt": d["createdAt"].isoformat(),
            }
            for d in duplicates
        ]


# AnswerSuggestionService
class AnswerSuggestionService(IAnswerSuggestionService):

    # Minimum similarity for using another forum reply as RAG context
    AI_CONTEXT_THRESHOLD: float = 0.72
    AI_CONTEXT_RELATIVE_GAP: float = 0.10

    # Template (not str.format) so LaTeX/braces in context do not break the prompt
    _ANSWER_PROMPT = Template("""Eres un asistente académico del programa de Ingeniería de Sistemas de la Universidad de Pamplona.
Tu rol es SUGERIR un punto de partida para la discusión en el foro, NO dar una respuesta definitiva.
Redacta una respuesta inicial en español sobre el tema de la pregunta del estudiante.

REGLAS IMPORTANTES:
- Responde SOLO sobre el tema del título y contenido de la pregunta del foro.
- Si el contexto recuperado habla de otro tema (ej. matemáticas/derivadas cuando la pregunta es de programación/POO), IGNÓRALO por completo.
- No mezcles conceptos de hilos no relacionados del foro.
- Si el contexto no aplica, explica el tema de la pregunta con conocimiento general de Ingeniería de Sistemas.
Al final, invita explícitamente a los demás estudiantes a complementar o debatir la respuesta.

Pregunta del foro:
Título: $title
Contenido: $content
Etiquetas: $tags

Contexto recuperado (puede estar vacío o ser parcial):
$context

Respuesta sugerida (máximo 300 palabras, en español, termina con una invitación al debate):""")

    def suggestAnswersForPost(self, postId: str, topK: int) -> List[Dict[str, Any]]:
        # Returns the topK most similar existing replies for a given post
        post = ForumPost.get_by_id(postId)
        if not post:
            print(f"[DEBUG] AnswerSuggestionService.suggestAnswersForPost -> post {postId} not found")
            return []

        query = ForumSemanticHelpers.buildPostText(
            post.get("title", ""),
            post.get("content", ""),
            post.get("tags", []),
        )

        searchSvc  = SemanticSearchService()
        candidates = searchSvc.findRelevantReplies(query, topK=topK, scoreThreshold=0.50)

        print(f"[DEBUG] AnswerSuggestionService.suggestAnswersForPost -> {len(candidates)} candidates")
        return candidates

    @staticmethod
    def _normalizeTags(tags: Optional[List[str]]) -> List[str]:
        if not tags:
            return []
        flat = []
        for tag in tags:
            for part in str(tag).replace(",", "\n").splitlines():
                cleaned = part.strip().lstrip("- ").strip()
                if cleaned:
                    flat.append(cleaned)
        return flat

    def _buildAnswerPrompt(self, title: str, content: str, tags: List[str], context: str) -> str:
        tags_label = ", ".join(tags) if tags else "(sin etiquetas)"
        return self._ANSWER_PROMPT.safe_substitute(
            title=title,
            content=content,
            tags=tags_label,
            context=context,
        )

    def _retrieveAiContext(self, postId: str, title: str, content: str, tags: List[str]) -> str:
        """Builds RAG context from forum replies and, if needed, academic books."""
        query_text = ForumSemanticHelpers.buildPostText(title, content, tags)
        embedding  = AIManager.get_embedding_service().embed(query_text)

        raw       = ForumEmbedding.search_answers(embedding, n_results=10)
        fragments = ForumSemanticHelpers.parseChromaResults(raw)

        scored = []
        current_post_id = str(postId)
        for item in fragments:
            meta = item["metadata"]
            if str(meta.get("postId", "")) == current_post_id:
                continue
            similarity = ForumSemanticHelpers.distanceToSimilarity(item["distance"])
            scored.append({
                "document":   item["document"],
                "similarity": similarity,
            })

        forum_parts = []
        if scored:
            scored.sort(key=lambda x: x["similarity"], reverse=True)
            top_sim   = scored[0]["similarity"]
            min_sim   = max(self.AI_CONTEXT_THRESHOLD, top_sim - self.AI_CONTEXT_RELATIVE_GAP)
            forum_parts = [
                item["document"]
                for item in scored
                if item["similarity"] >= min_sim
            ][:3]
            print(
                f"[DEBUG] AnswerSuggestionService._retrieveAiContext -> "
                f"forum fragments: {len(forum_parts)} (min_sim={min_sim:.2f})"
            )

        if forum_parts:
            return "Respuestas relacionadas del foro:\n" + "\n\n---\n\n".join(forum_parts)

        from assistant.services.rag_service import RAGService
        book_context, _ = RAGService().retrieve_context(query_text, k=3)
        if book_context.strip():
            print("[DEBUG] AnswerSuggestionService._retrieveAiContext -> using academic books fallback")
            return "Material académico indexado:\n" + book_context

        return "Sin contexto externo relevante. Responde solo con el tema de la pregunta del estudiante."

    def generateAiAnswer(
        self,
        postId: str,
        title: str,
        content: str,
        tags: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        # RAG pipeline: embed -> retrieve -> prompt -> generate -> persist -> index
        print(f"[DEBUG] AnswerSuggestionService.generateAiAnswer -> postId: {postId}")

        llmSvc = AIManager.get_llm_service()
        tags   = self._normalizeTags(tags)

        context       = self._retrieveAiContext(postId, title, content, tags)
        prompt        = self._buildAnswerPrompt(title, content, tags, context)
        generatedText = llmSvc.generate(prompt)

        print(f"[DEBUG] AnswerSuggestionService.generateAiAnswer -> LLM response received")

        # Reserved sentinel mapped to "Asistente Académico IA" in the view layer
        AI_AUTHOR_ID = "000000000000000000000000"

        replyId = ForumReply.create(
            postId      = postId,
            authorId    = AI_AUTHOR_ID,
            content     = generatedText,
            aiGenerated = True,
        )

        # Index the AI reply so it can surface in future searches
        SemanticIndexService().indexReply(replyId, postId, generatedText)

        return {
            "replyId":     replyId,
            "postId":      postId,
            "content":     generatedText,
            "aiGenerated": True,
        }

    def rankReplies(self, postId: str, replies: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        # Re-ranks replies by: (similarity * 0.6) + (voteScore * 0.3) + (isAccepted * 0.1)
        post = ForumPost.get_by_id(postId)
        if not post or not replies:
            return replies

        embeddingSvc   = AIManager.get_embedding_service()
        queryText      = ForumSemanticHelpers.buildPostText(
            post.get("title", ""),
            post.get("content", ""),
            post.get("tags", []),
        )
        queryEmbedding = embeddingSvc.embed(queryText)

        # Build replyId -> similarity via dot product (BGE-M3 vectors are L2-normalised)
        similarities = {}
        for reply in replies:
            replyId = reply.get("id", reply.get("replyId", ""))
            repEmb  = embeddingSvc.embed(reply.get("content", ""))
            dot     = sum(a * b for a, b in zip(queryEmbedding, repEmb))
            similarities[replyId] = max(0.0, min(1.0, dot))

        # Normalise vote scores to [0, 1]
        scores   = [abs(r.get("score", 0.0)) for r in replies]
        maxScore = max(scores) if scores and max(scores) > 0 else 1.0

        ranked = []
        for reply in replies:
            replyId  = reply.get("id", reply.get("replyId", ""))
            sim      = similarities.get(replyId, 0.0)
            voteNorm = abs(reply.get("score", 0.0)) / maxScore
            accepted = 1.0 if reply.get("isAccepted") else 0.0
            final    = (sim * 0.6) + (voteNorm * 0.3) + (accepted * 0.1)

            ranked.append({**reply, "_rankScore": round(final, 4)})

        ranked.sort(key=lambda x: x["_rankScore"], reverse=True)
        print(f"[DEBUG] AnswerSuggestionService.rankReplies -> ranked {len(ranked)} replies")
        return ranked


# QueryExpansionService
class QueryExpansionService(IQueryExpansionService):

    # LLM prompt for semantic query reformulation
    _EXPAND_PROMPT = """Eres un asistente académico especializado en Ingeniería de Sistemas.
                    Reformula la siguiente consulta estudiantil en español para mejorar su precisión en una búsqueda semántica.
                    Genera UNA sola reformulación más completa y técnica (máximo 2 oraciones).
                    No respondas la pregunta; solo reformúlala.

Consulta original: {query}

Reformulación:"""

    # LLM prompt for tag suggestion on new posts
    _KEYTERM_PROMPT = """Extrae los conceptos clave más relevantes del siguiente texto académico.
Devuelve SOLO una lista de términos separados por comas, sin numeración ni explicaciones.
Máximo 6 términos. Prioriza sustantivos técnicos en español.

Texto: {text}

Términos clave:"""

    _STOPWORDS = {
        "de", "la", "el", "en", "y", "a", "los", "del", "las", "un",
        "una", "con", "por", "para", "es", "se", "que", "no", "al",
        "lo", "su", "le", "más", "pero", "como", "o", "si", "ya",
        "me", "mi", "te", "tu", "hay", "ser", "este", "esta", "son",
    }

    def expandQuery(self, rawQuery: str) -> str:
        # Reformulates the query via LLM; falls back to normalizeQuery on failure
        print(f"[DEBUG] QueryExpansionService.expandQuery -> rawQuery: '{rawQuery}'")

        normalized = self.normalizeQuery(rawQuery)

        try:
            llmSvc   = AIManager.get_llm_service()
            prompt   = self._EXPAND_PROMPT.format(query=normalized)
            expanded = llmSvc.generate(prompt).strip()

            if len(expanded) < 10:
                raise ValueError("LLM returned an empty or too-short expansion")

            print(f"[DEBUG] QueryExpansionService.expandQuery -> expanded: '{expanded}'")
            return expanded

        except Exception as e:
            print(f"[ERROR] QueryExpansionService.expandQuery -> LLM failed: {e}. Using normalized query.")
            return normalized

    def extractKeyTerms(self, text: str) -> List[str]:
        # Uses the LLM to extract key terms; falls back to frequency-based extraction
        print(f"[DEBUG] QueryExpansionService.extractKeyTerms -> text length: {len(text)}")

        try:
            llmSvc = AIManager.get_llm_service()
            prompt = self._KEYTERM_PROMPT.format(text=text[:1500])
            raw    = llmSvc.generate(prompt)
            terms  = [t.strip() for t in raw.split(",") if t.strip()]

            print(f"[DEBUG] QueryExpansionService.extractKeyTerms -> {terms}")
            return terms[:6]

        except Exception as e:
            print(f"[ERROR] QueryExpansionService.extractKeyTerms -> LLM failed: {e}. Using fallback.")
            return self._fallbackKeyTerms(text)

    def normalizeQuery(self, rawQuery: str) -> str:
        # Lowercases, strips Spanish punctuation noise, and collapses whitespace
        normalized = rawQuery.strip().lower()
        normalized = re.sub(r"[¿¡]", "", normalized)
        normalized = re.sub(r"[^\w\sáéíóúüñ.,;:?!-]", " ", normalized)
        normalized = re.sub(r"\s+", " ", normalized).strip()

        print(f"[DEBUG] QueryExpansionService.normalizeQuery -> '{rawQuery}' -> '{normalized}'")
        return normalized

    def _fallbackKeyTerms(self, text: str) -> List[str]:
        # Returns the 6 most frequent content words after removing Spanish stopwords
        words   = re.findall(r"\b\w{4,}\b", text.lower())
        content = [w for w in words if w not in self._STOPWORDS]
        common  = Counter(content).most_common(6)
        return [word for word, _ in common]
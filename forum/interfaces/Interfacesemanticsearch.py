from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


# Embedding indexing interface
# Responsible for building and maintaining the vector store

class ISemanticIndexService(ABC):

    @abstractmethod
    def indexPost(self, postId: str, title: str, content: str, tags: List[str]) -> bool:
        # Embed and store a forum post so it is searchable by similarity
        pass

    @abstractmethod
    def updateIndexedPost(self, postId: str, title: str, content: str, tags: List[str]) -> bool:
        # Re-embed a post after it has been edited and update the vector store
        pass

    @abstractmethod
    def removeIndexedPost(self, postId: str) -> bool:
        # Delete a post's vector from the store when the post is removed
        pass

    @abstractmethod
    def indexReply(self, replyId: str, postId: str, content: str) -> bool:
        # Embed and store a reply so it can surface as a relevant answer
        pass

    @abstractmethod
    def removeIndexedReply(self, replyId: str) -> bool:
        # Delete a reply's vector from the store when the reply is removed
        pass

    @abstractmethod
    def rebuildIndex(self) -> int:
        # Drop and fully rebuild the vector store from the database; returns count indexed
        pass


# Similarity search interface
# Responsible for querying the vector store and returning ranked results

class ISemanticSearchService(ABC):

    @abstractmethod
    def findSimilarPosts(
        self,
        queryText: str,
        topK: int,
        scoreThreshold: float,
    ) -> List[Dict[str, Any]]:
        # Return the top-K posts most semantically similar to the input query
        # Each result includes postId, title, and similarity score
        pass

    @abstractmethod
    def findSimilarPostById(
        self,
        postId: str,
        topK: int,
        scoreThreshold: float,
    ) -> List[Dict[str, Any]]:
        # Find posts similar to an existing post using its stored embedding
        pass

    @abstractmethod
    def findRelevantReplies(
        self,
        queryText: str,
        topK: int,
        scoreThreshold: float,
    ) -> List[Dict[str, Any]]:
        # Retrieve replies whose content is semantically close to the query
        # Useful for surfacing accepted answers to new questions
        pass

    @abstractmethod
    def searchByTags(
        self,
        tags: List[str],
        queryText: Optional[str],
        topK: int,
    ) -> List[Dict[str, Any]]:
        # Combine tag filtering with optional vector similarity ranking
        pass



# Duplicate detection interface
# Responsible for identifying whether a new post already exists in the forum

class IDuplicateDetectionService(ABC):

    @abstractmethod
    def detectDuplicates(
        self,
        title: str,
        content: str,
        scoreThreshold: float,
    ) -> List[Dict[str, Any]]:
        # Return candidate posts that are likely duplicates of the given text
        # Each result includes postId, title, similarity score, and status
        pass

    @abstractmethod
    def isClearDuplicate(self, title: str, content: str, hardThreshold: float) -> bool:
        # Return True when the top similarity score exceeds the hard threshold
        # Used as a fast pre-check before a user submits a post
        pass

    @abstractmethod
    def confirmDuplicate(self, postId: str, originalPostId: str) -> Dict[str, Any]:
        # Persist the duplicate link between posts and update their statuses
        pass

    @abstractmethod
    def getDuplicatesOfPost(self, originalPostId: str) -> List[Dict[str, Any]]:
        # Return all posts that have been confirmed as duplicates of the given post
        pass



# AI answer suggestion interface
# Responsible for generating or retrieving relevant answers for a question

class IAnswerSuggestionService(ABC):

    @abstractmethod
    def suggestAnswersForPost(
        self,
        postId: str,
        topK: int,
    ) -> List[Dict[str, Any]]:
        # Retrieve the most semantically relevant existing replies for a post
        # Results are ordered by similarity and can be shown as suggested answers
        pass

    @abstractmethod
    def generateAiAnswer(self, postId: str, title: str, content: str) -> Dict[str, Any]:
        # Use the LLM + RAG pipeline to draft an AI-generated reply for a post
        # Returns the generated content and metadata to persist as a ForumReply
        pass

    @abstractmethod
    def rankReplies(self, postId: str, replies: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        # Re-rank a list of replies by semantic relevance to the parent post
        pass



# Query expansion interface
# Responsible for enriching user queries before similarity search

class IQueryExpansionService(ABC):

    @abstractmethod
    def expandQuery(self, rawQuery: str) -> str:
        # Reformulate or expand the raw query to improve recall in vector search
        # May use synonym injection, question paraphrasing, or LLM rewriting
        pass

    @abstractmethod
    def extractKeyTerms(self, text: str) -> List[str]:
        # Pull out the most relevant keywords or concepts from a block of text
        # Used to suggest tags when a user creates a new post
        pass

    @abstractmethod
    def normalizeQuery(self, rawQuery: str) -> str:
        # Clean, lower-case, and strip noise from a query before embedding it
        pass
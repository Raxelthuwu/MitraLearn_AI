# Forum domain interfaces
from .Interfaceforum import (
    IForumCategoryService,
    IForumSubcategoryService,
    IForumTopicService,
    IForumPostService,
    IForumReplyService,
    IForumVoteService,
    IForumBookmarkService,
    IForumNotificationService,
)

# Semantic search and AI interfaces
from .Interfacesemanticsearch import (
    ISemanticIndexService,
    ISemanticSearchService,
    IDuplicateDetectionService,
    IAnswerSuggestionService,
    IQueryExpansionService,
)

__all__ = [
    # Forum
    "IForumCategoryService",
    "IForumSubcategoryService",
    "IForumTopicService",
    "IForumPostService",
    "IForumReplyService",
    "IForumVoteService",
    "IForumBookmarkService",
    "IForumNotificationService",
    # Semantic search
    "ISemanticIndexService",
    "ISemanticSearchService",
    "IDuplicateDetectionService",
    "IAnswerSuggestionService",
    "IQueryExpansionService",
]
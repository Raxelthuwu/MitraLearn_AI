import os
import uuid
from pathlib import Path

from django.conf import settings
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from assistant.Assistant_vector_models import ChatEmbedding
from assistant.models import IndexedBook
from core.ai_manager import AIManager


class IngestionService:
    """PDF upload, chunking, and indexing into chat_embeddings."""

    def __init__(self):
        self.embedding_service = AIManager.get_embedding_service()
        os.makedirs(settings.CHAT_UPLOAD_DIR, exist_ok=True)

    def process_pdf(self, uploaded_file, subcategory_id: str, topic_id: str = None, uploaded_by: str = None):
        if not uploaded_file or not uploaded_file.name.lower().endswith(".pdf"):
            raise ValueError("Se requiere un archivo PDF válido.")

        sub_dir = os.path.join(settings.CHAT_UPLOAD_DIR, str(subcategory_id))
        os.makedirs(sub_dir, exist_ok=True)

        safe_name = Path(uploaded_file.name).name
        stored_name = f"{uuid.uuid4().hex}_{safe_name}"
        stored_path = os.path.join(sub_dir, stored_name)

        with open(stored_path, "wb") as dest:
            for chunk in uploaded_file.chunks():
                dest.write(chunk)

        loader = PyPDFLoader(stored_path)
        pages = loader.load()

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=getattr(settings, "CHAT_CHUNK_SIZE", 800),
            chunk_overlap=getattr(settings, "CHAT_CHUNK_OVERLAP", 120),
        )
        chunks = splitter.split_documents(pages)

        book_id = str(uuid.uuid4())
        texts = [c.page_content for c in chunks]
        embeddings = self.embedding_service.embed_documents(texts)

        indexed = 0
        for i, (chunk_doc, embedding) in enumerate(zip(chunks, embeddings)):
            page = chunk_doc.metadata.get("page", 0)
            if isinstance(page, (int, float)):
                page_num = int(page) + 1
            else:
                page_num = 0

            chunk_id = f"book_{book_id}_chunk_{i}"
            ChatEmbedding.add(
                chunk_id=chunk_id,
                embedding=embedding,
                document_text=chunk_doc.page_content,
                source=safe_name,
                page=page_num,
                subcategory_id=subcategory_id,
                topic_id=topic_id,
                book_id=book_id,
            )
            indexed += 1

        IndexedBook.create(
            filename=safe_name,
            subcategoryId=subcategory_id,
            topicId=topic_id,
            chunkCount=indexed,
            uploadedBy=uploaded_by or "",
            storedPath=stored_path,
        )

        return {
            "bookId": book_id,
            "filename": safe_name,
            "chunkCount": indexed,
            "storedPath": stored_path,
        }

    def get_uploaded_books(self, subcategory_id: str):
        books = IndexedBook.get_by_subcategory(subcategory_id)
        return [
            {
                "bookId": b["bookId"],
                "filename": b["filename"],
                "chunkCount": b.get("chunkCount", 0),
                "topicId": str(b["topicId"]) if b.get("topicId") else None,
                "createdAt": b["createdAt"].isoformat(),
            }
            for b in books
        ]

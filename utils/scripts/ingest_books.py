import os
import sys
from pathlib import Path

# Add project root to sys.path (two levels up now)
BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(BASE_DIR))

import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.base')
django.setup()

from django.conf import settings
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from core import AIManager

def ingest_pdfs():
    """
    Ingests PDFs into the official 'chat_embeddings' collection
    using the unified AI motor.
    """
    books_dir = os.path.join(settings.BASE_DIR, "data", "books")
    
    if not os.path.exists(books_dir):
        print(f"[ERROR] Directory not found: {books_dir}")
        return

    # Initialize Services (Unified Motor)
    print("[INFO] Initializing Unified AI Services...")
    embedding_service = AIManager.get_embedding_service()
    
    # Initialize Vector DB in the official shared path
    # Collection name synced to 'chat_embeddings'
    vector_db = Chroma(
        persist_directory=settings.CHROMA_PATH,
        embedding_function=embedding_service.embeddings,
        collection_name="chat_embeddings"
    )

    pdf_files = [f for f in os.listdir(books_dir) if f.endswith('.pdf')]
    
    if not pdf_files:
        print("[WARNING] No PDF files found in data/books/.")
        return

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        add_start_index=True
    )

    for pdf_file in pdf_files:
        file_path = os.path.join(books_dir, pdf_file)
        print(f"[PROCESS] Ingesting into 'chat_embeddings': {pdf_file}...")
        
        try:
            loader = PyPDFLoader(file_path)
            pages = loader.load()
            chunks = text_splitter.split_documents(pages)
            
            vector_db.add_documents(chunks)
            print(f"[SUCCESS] {pdf_file} has been indexed.")
            
        except Exception as e:
            print(f"[ERROR] Failed to process {pdf_file}: {e}")

    print("\n[FINISH] Ingestion into shared vector DB complete.")

if __name__ == "__main__":
    ingest_pdfs()

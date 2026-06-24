"""
Indexa los PDF de data/books en ChromaDB (colección chat_embeddings).

Uso:
  python utils/scripts/ingest_books.py
  python utils/scripts/ingest_books.py --subcategory-id <ObjectId>
  python utils/scripts/ingest_books.py --from-catalog
"""
import argparse
import os
import sys
import uuid
from pathlib import Path
from typing import Optional

BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE_DIR))

from dotenv import load_dotenv

load_dotenv(BASE_DIR / ".env")

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

from django.conf import settings
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from assistant.Assistant_vector_models import ChatEmbedding
from assistant.models import IndexedBook
from core import AIManager


def _get_splitter() -> RecursiveCharacterTextSplitter:
    return RecursiveCharacterTextSplitter(
        chunk_size=getattr(settings, "CHAT_CHUNK_SIZE", 800),
        chunk_overlap=getattr(settings, "CHAT_CHUNK_OVERLAP", 120),
        add_start_index=True,
    )


def ingest_pdf_file(
    file_path: Path,
    subcategory_id: Optional[str] = None,
    topic_id: Optional[str] = None,
    embedding_service=None,
    splitter: Optional[RecursiveCharacterTextSplitter] = None,
) -> int:
    """Indexa un solo PDF. Devuelve cantidad de fragmentos creados."""
    file_path = Path(file_path)
    pdf_file = file_path.name

    if embedding_service is None:
        embedding_service = AIManager.get_embedding_service()
    if splitter is None:
        splitter = _get_splitter()

    print(f"[PROCESS] Indexando: {pdf_file}")

    loader = PyPDFLoader(str(file_path))
    pages = loader.load()
    chunks = splitter.split_documents(pages)

    if not chunks:
        print(f"[WARNING] Sin contenido extraíble: {pdf_file}")
        return 0

    texts = [c.page_content for c in chunks]
    embeddings = embedding_service.embed_documents(texts)

    book_id = str(uuid.uuid4())
    indexed = 0

    for i, (chunk_doc, embedding) in enumerate(zip(chunks, embeddings)):
        page = chunk_doc.metadata.get("page", 0)
        page_num = int(page) + 1 if isinstance(page, (int, float)) else 0
        chunk_id = f"book_{book_id}_chunk_{i}"

        ChatEmbedding.add(
            chunk_id=chunk_id,
            embedding=embedding,
            document_text=chunk_doc.page_content,
            source=pdf_file,
            page=page_num,
            subcategory_id=subcategory_id,
            topic_id=topic_id,
            book_id=book_id,
        )
        indexed += 1

    if subcategory_id:
        IndexedBook.create(
            filename=pdf_file,
            subcategoryId=subcategory_id,
            topicId=topic_id,
            chunkCount=indexed,
            uploadedBy="",
            storedPath=str(file_path),
        )

    print(f"[SUCCESS] {pdf_file} → {indexed} fragmentos indexados")
    return indexed


def ingest_pdfs(subcategory_id: str = None, topic_id: str = None) -> None:
    books_dir = BASE_DIR / "data" / "books"

    if not books_dir.exists():
        books_dir.mkdir(parents=True, exist_ok=True)
        print(f"[ERROR] Carpeta creada pero vacía: {books_dir}")
        print("        Coloca tus archivos .pdf ahí y vuelve a ejecutar el script.")
        return

    pdf_files = sorted(f for f in os.listdir(books_dir) if f.lower().endswith(".pdf"))

    if not pdf_files:
        print(f"[WARNING] No hay PDF en {books_dir}")
        return

    print("[INFO] Cargando modelo de embeddings (puede tardar)...")
    embedding_service = AIManager.get_embedding_service()
    splitter = _get_splitter()

    total_chunks = 0

    for pdf_file in pdf_files:
        file_path = books_dir / pdf_file
        try:
            total_chunks += ingest_pdf_file(
                file_path=file_path,
                subcategory_id=subcategory_id,
                topic_id=topic_id,
                embedding_service=embedding_service,
                splitter=splitter,
            )
        except Exception as e:
            print(f"[ERROR] Falló {pdf_file}: {e}")

    print(f"\n[FINISH] Ingesta completa. Total fragmentos: {total_chunks}")


def ingest_from_catalog() -> None:
    from utils.scripts.book_catalog import list_catalog_entries_on_disk
    from utils.scripts.seed_chat_subjects import seed_catalog

    print("[INFO] Asegurando materias y temas en MongoDB ...")
    mapping = seed_catalog()

    found, missing = list_catalog_entries_on_disk()
    if missing:
        print("\n[AVISO] PDF no encontrados en data/books:")
        for name in missing:
            print(f"        - {name}")

    if not found:
        print("\n[ERROR] No hay PDF para indexar.")
        return

    print("\n[INFO] Cargando modelo de embeddings (puede tardar)...")
    embedding_service = AIManager.get_embedding_service()
    splitter = _get_splitter()

    total_chunks = 0
    for entry in found:
        ids = mapping.get(entry["filename"], {})
        try:
            total_chunks += ingest_pdf_file(
                file_path=entry["path"],
                subcategory_id=ids.get("subcategoryId"),
                topic_id=ids.get("topicId"),
                embedding_service=embedding_service,
                splitter=splitter,
            )
        except Exception as e:
            print(f"[ERROR] Falló {entry['filename']}: {e}")

    print(f"\n[FINISH] Ingesta por catálogo completa. Total fragmentos: {total_chunks}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Indexa PDFs de data/books en ChromaDB")
    parser.add_argument(
        "--subcategory-id",
        default=None,
        help="ID de subcategoría (materia) para filtrar búsquedas en el chat",
    )
    parser.add_argument(
        "--topic-id",
        default=None,
        help="ID de tópico opcional",
    )
    parser.add_argument(
        "--from-catalog",
        action="store_true",
        help="Indexa cada PDF con la materia y tema definidos en book_catalog.py",
    )
    args = parser.parse_args()

    if args.from_catalog:
        ingest_from_catalog()
    else:
        ingest_pdfs(subcategory_id=args.subcategory_id, topic_id=args.topic_id)


if __name__ == "__main__":
    main()

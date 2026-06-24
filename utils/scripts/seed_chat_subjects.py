"""
Crea materias (subcategorías) y temas en MongoDB a partir de los libros en data/books.

El chat del asistente usa ForumSubcategory como "Materia" y ForumTopic como "Tema".

Uso:
  python utils/scripts/seed_chat_subjects.py
  python utils/scripts/seed_chat_subjects.py --ingest   # también indexa PDFs en ChromaDB
"""
import argparse
import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE_DIR))

from dotenv import load_dotenv

load_dotenv(BASE_DIR / ".env")

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

from bson import ObjectId

from forum.models import ForumCategory, ForumSubcategory, ForumTopic
from utils.scripts.book_catalog import BOOK_CATALOG, list_catalog_entries_on_disk


def _find_category(name: str):
    return ForumCategory.collection.find_one({"name": name})


def _find_subcategory(category_id: ObjectId, name: str):
    return ForumSubcategory.collection.find_one({
        "categoryId": category_id,
        "name": name,
    })


def _find_topic(subcategory_id: ObjectId, name: str):
    return ForumTopic.collection.find_one({
        "subcategoryId": subcategory_id,
        "name": name,
    })


def get_or_create_category(name: str, description: str = "") -> str:
    existing = _find_category(name)
    if existing:
        return str(existing["_id"])
    return ForumCategory.create(name=name, description=description)


def get_or_create_subject(category_id: str, name: str) -> str:
    cat_oid = ObjectId(category_id)
    existing = _find_subcategory(cat_oid, name)
    if existing:
        return str(existing["_id"])
    return ForumSubcategory.create(categoryId=category_id, name=name)


def get_or_create_topic(subcategory_id: str, name: str) -> str:
    sub_oid = ObjectId(subcategory_id)
    existing = _find_topic(sub_oid, name)
    if existing:
        return str(existing["_id"])
    return ForumTopic.create(subcategoryId=subcategory_id, name=name)


def seed_catalog() -> dict:
    """
    Inserta categorías, materias y temas. Devuelve mapa filename → ids.
    """
    mapping = {}
    categories_done = set()
    subjects_done = set()

    print("[INFO] Sembrando materias y temas desde book_catalog.py ...\n")

    for entry in BOOK_CATALOG:
        cat_name = entry["category"]
        if cat_name not in categories_done:
            cat_id = get_or_create_category(cat_name, entry.get("category_description", ""))
            print(f"[OK] Categoría: {cat_name} ({cat_id})")
            categories_done.add(cat_name)
        else:
            cat_id = str(_find_category(cat_name)["_id"])

        subject_key = (cat_id, entry["subject"])
        if subject_key not in subjects_done:
            sub_id = get_or_create_subject(cat_id, entry["subject"])
            print(f"     Materia: {entry['subject']} ({sub_id})")
            subjects_done.add(subject_key)
        else:
            sub_id = str(_find_subcategory(ObjectId(cat_id), entry["subject"])["_id"])

        topic_id = get_or_create_topic(sub_id, entry["topic"])
        print(f"       Tema: {entry['topic']} ({topic_id})")
        print(f"       Libro: {entry['filename']}\n")

        mapping[entry["filename"]] = {
            "categoryId": cat_id,
            "subcategoryId": sub_id,
            "topicId": topic_id,
            "subject": entry["subject"],
            "topic": entry["topic"],
        }

    return mapping


def run_ingest(mapping: dict) -> None:
    from utils.scripts.ingest_books import ingest_pdf_file

    found, missing = list_catalog_entries_on_disk()

    if missing:
        print("[AVISO] PDF no encontrados en data/books:")
        for name in missing:
            print(f"        - {name}")
        print()

    if not found:
        print("[ERROR] No hay PDF en data/books. Coloca los libros y vuelve a ejecutar con --ingest.")
        return

    print(f"[INFO] Indexando {len(found)} libro(s) en ChromaDB ...\n")
    total = 0
    for entry in found:
        ids = mapping.get(entry["filename"], {})
        sub_id = ids.get("subcategoryId")
        topic_id = ids.get("topicId")
        chunks = ingest_pdf_file(
            file_path=entry["path"],
            subcategory_id=sub_id,
            topic_id=topic_id,
        )
        total += chunks

    print(f"\n[FINISH] Indexación completa. Total fragmentos: {total}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Crea materias y temas del chat según los libros en data/books",
    )
    parser.add_argument(
        "--ingest",
        action="store_true",
        help="Tras sembrar MongoDB, indexa cada PDF con su materia y tema",
    )
    args = parser.parse_args()

    mapping = seed_catalog()

    subjects = ForumSubcategory.get_all()
    topics = ForumTopic.get_all()
    print(f"[RESUMEN] {len(subjects)} materia(s), {len(topics)} tema(s) en total.\n")

    if args.ingest:
        run_ingest(mapping)
    else:
        print("Para indexar los PDF en ChromaDB ejecuta:")
        print("  python utils/scripts/seed_chat_subjects.py --ingest")
        print("  # o: python utils/scripts/ingest_books.py --from-catalog")


if __name__ == "__main__":
    main()

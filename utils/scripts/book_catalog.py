"""
Catálogo de libros en data/books → categoría, materia (subcategoría) y tema.

Usado por seed_chat_subjects.py e ingest_books.py (--from-catalog).
"""
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
BOOKS_DIR = BASE_DIR / "data" / "books"

# category → materia (subcategory) → topic + archivo PDF
BOOK_CATALOG = [
    {
        "filename": "0185-programacion-orientada-a-objetos.pdf",
        "category": "Ciencias de la Computación",
        "category_description": "Programación, bases de datos e ingeniería de software.",
        "subject": "Programación",
        "topic": "Programación orientada a objetos",
    },
    {
        "filename": "Introduccion a la Programacion Orientada a Objetos.pdf",
        "category": "Ciencias de la Computación",
        "category_description": "Programación, bases de datos e ingeniería de software.",
        "subject": "Programación",
        "topic": "Introducción a POO",
    },
    {
        "filename": "Fundamentos_de_programación_4ta_Edición_Luis_Joyanes_Aguilar_2.pdf",
        "category": "Ciencias de la Computación",
        "category_description": "Programación, bases de datos e ingeniería de software.",
        "subject": "Programación",
        "topic": "Fundamentos de programación",
    },
    {
        "filename": "Fundamentos De Bases De Datos (Autor  Silberschatz, Abraham ) (Editorial, Mc Graw Hill).pdf",
        "category": "Ciencias de la Computación",
        "category_description": "Programación, bases de datos e ingeniería de software.",
        "subject": "Bases de datos",
        "topic": "Modelo relacional y diseño",
    },
    {
        "filename": "toaz.info-ingenieria-de-software-orientado-a-objetos-bernd-bruegge-librosvirtualpdf-pr_83182e13a0.pdf",
        "category": "Ciencias de la Computación",
        "category_description": "Programación, bases de datos e ingeniería de software.",
        "subject": "Ingeniería de software",
        "topic": "Diseño orientado a objetos",
    },
    {
        "filename": "calculo_diferencial_integral_func_una_var.pdf",
        "category": "Matemáticas",
        "category_description": "Cálculo y matemáticas discretas.",
        "subject": "Cálculo",
        "topic": "Cálculo de una variable",
    },
    {
        "filename": "stewart.pdf",
        "category": "Matemáticas",
        "category_description": "Cálculo y matemáticas discretas.",
        "subject": "Cálculo",
        "topic": "Cálculo (Stewart)",
    },
    {
        "filename": "matematicasdiscretas1.pdf",
        "category": "Matemáticas",
        "category_description": "Cálculo y matemáticas discretas.",
        "subject": "Matemáticas discretas",
        "topic": "Lógica, conjuntos y grafos",
    },
    {
        "filename": "Libro-fisica-para-ciencias-e-ingenieria-serway-7ed-vol-2.pdf",
        "category": "Ciencias básicas",
        "category_description": "Física y fundamentos para ingeniería.",
        "subject": "Física",
        "topic": "Electricidad y magnetismo",
    },
]


def resolve_book_path(filename: str) -> Path:
    """Devuelve la ruta del PDF si existe en data/books (coincidencia exacta o por nombre)."""
    exact = BOOKS_DIR / filename
    if exact.is_file():
        return exact

    if not BOOKS_DIR.is_dir():
        return exact

    target = filename.lower()
    for path in BOOKS_DIR.iterdir():
        if path.is_file() and path.name.lower() == target:
            return path
    return exact


def list_catalog_entries_on_disk():
    """Entradas del catálogo cuyo PDF está presente en data/books."""
    found = []
    missing = []
    for entry in BOOK_CATALOG:
        path = resolve_book_path(entry["filename"])
        if path.is_file():
            found.append({**entry, "path": path})
        else:
            missing.append(entry["filename"])
    return found, missing

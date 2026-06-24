import urllib.parse
import xml.etree.ElementTree as ET

import requests

from core.ai_manager import AIManager


class ExternalSearchService:
    """Fallback search via Wikipedia and ArXiv when local RAG context is insufficient."""

    _PROMPT = """Eres un asistente académico. Responde en español usando el contexto externo.
Indica que la información proviene de una fuente externa ({source}).
Al final invita al estudiante a contrastar con el material del curso.

Contexto externo:
{context}

Pregunta: {query}

Respuesta:"""

    def __init__(self):
        self.llm = AIManager.get_llm_service()

    def search_wikipedia(self, query: str, lang: str = "es", sentences: int = 4) -> str:
        params = {
            "action": "query",
            "prop": "extracts",
            "exintro": True,
            "explaintext": True,
            "format": "json",
            "titles": query,
            "redirects": 1,
        }
        url = f"https://{lang}.wikipedia.org/w/api.php?{urllib.parse.urlencode(params)}"
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        pages = data.get("query", {}).get("pages", {})
        for page in pages.values():
            extract = page.get("extract", "")
            if extract:
                return extract[:2000]
        return ""

    def search_arxiv(self, query: str, max_results: int = 2) -> str:
        params = {
            "search_query": f"all:{query}",
            "start": 0,
            "max_results": max_results,
        }
        url = f"http://export.arxiv.org/api/query?{urllib.parse.urlencode(params)}"
        resp = requests.get(url, timeout=12)
        resp.raise_for_status()
        root = ET.fromstring(resp.text)
        ns = {"atom": "http://www.w3.org/2005/Atom"}
        parts = []
        for entry in root.findall("atom:entry", ns):
            title = entry.find("atom:title", ns)
            summary = entry.find("atom:summary", ns)
            t = title.text.strip() if title is not None and title.text else ""
            s = summary.text.strip() if summary is not None and summary.text else ""
            if t or s:
                parts.append(f"Título: {t}\nResumen: {s[:600]}")
        return "\n\n".join(parts)

    def generate_external_response(self, query: str, source: str = "wikipedia") -> dict:
        source = (source or "wikipedia").lower()
        if source == "arxiv":
            context = self.search_arxiv(query)
            label = "ArXiv"
        else:
            context = self.search_wikipedia(query)
            label = "Wikipedia"

        if not context.strip():
            return {
                "answer": "No se encontró información externa relevante para esta consulta.",
                "externalSource": label,
                "contextInsufficient": True,
            }

        prompt = self._PROMPT.format(source=label, context=context, query=query)
        answer = self.llm.generate(prompt)
        return {
            "answer": answer,
            "externalSource": label,
            "contextInsufficient": False,
        }

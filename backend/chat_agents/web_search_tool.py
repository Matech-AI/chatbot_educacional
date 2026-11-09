"""Busca na web para quando o acervo do curso não cobre a pergunta.

Usa Tavily quando TAVILY_API_KEY está definida (resultados melhores para LLMs);
caso contrário usa DuckDuckGo, que não exige chave.
Desligue com WEB_SEARCH_ENABLED=false.
"""
import logging
import os
from typing import Any, Dict, List, Type

import requests
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

WEB_SEARCH_TIMEOUT = float(os.getenv("WEB_SEARCH_TIMEOUT_SECONDS", "15"))
WEB_SEARCH_MAX_RESULTS = int(os.getenv("WEB_SEARCH_MAX_RESULTS", "5"))


def web_search_enabled() -> bool:
    return os.getenv("WEB_SEARCH_ENABLED", "true").lower() == "true"


class WebSearchInput(BaseModel):
    query: str = Field(description="Termos de busca, de preferência em português.")


def _search_tavily(query: str, api_key: str) -> List[Dict[str, str]]:
    resp = requests.post(
        "https://api.tavily.com/search",
        json={"api_key": api_key, "query": query,
              "max_results": WEB_SEARCH_MAX_RESULTS, "search_depth": "basic"},
        timeout=WEB_SEARCH_TIMEOUT,
    )
    resp.raise_for_status()
    return [{"title": r.get("title", ""), "url": r.get("url", ""), "snippet": r.get("content", "")}
            for r in resp.json().get("results", [])]


# Os buscadores gratuitos recusam requisições de forma aleatória (rate limit / anti-bot),
# então tentamos um após o outro até algum devolver resultados.
# "auto" consulta vários buscadores (Yahoo, Startpage, DuckDuckGo...) e mescla os resultados.
DDGS_BACKENDS = [b.strip() for b in os.getenv(
    "WEB_SEARCH_BACKENDS", "auto,yahoo,startpage,duckduckgo,wikipedia").split(",") if b.strip()]

# ddgs registra cada requisição interna em INFO; silencia para não poluir o log
for _noisy in ("ddgs", "primp"):
    logging.getLogger(_noisy).setLevel(logging.WARNING)


def _search_duckduckgo(query: str) -> List[Dict[str, str]]:
    from ddgs import DDGS

    last_error: Exception = RuntimeError("nenhum backend configurado")
    for backend in DDGS_BACKENDS:
        try:
            results = DDGS(timeout=int(WEB_SEARCH_TIMEOUT)).text(
                query, region="br-pt", max_results=WEB_SEARCH_MAX_RESULTS, backend=backend)
        except Exception as e:
            last_error = e
            logger.info(f"🌐 Web search backend '{backend}' failed: {e}")
            continue
        if results:
            logger.info(f"🌐 Web search backend '{backend}' returned {len(results)} results")
            return [{"title": r.get("title", ""), "url": r.get("href", ""),
                     "snippet": r.get("body", "")} for r in results]
    raise last_error


class WebSearchTool(BaseTool):
    name: str = "search_web"
    description: str = (
        "Busca na internet. Use SOMENTE quando 'search_educational_materials' não encontrar "
        "material do curso sobre a pergunta. Retorna títulos, links e trechos de páginas."
    )
    args_schema: Type[BaseModel] = WebSearchInput

    def _run(self, query: str) -> Dict[str, Any]:
        logger.info(f"🌐 Tool '{self.name}' invoked with query: '{query}'")
        tavily_key = os.getenv("TAVILY_API_KEY")
        # O modelo costuma montar buscas longas demais; se nada voltar, tenta uma versão curta.
        words = query.split()
        attempts = [query] + ([" ".join(words[:4])] if len(words) > 4 else [])
        results: List[Dict[str, str]] = []
        for attempt in attempts:
            try:
                results = _search_tavily(attempt, tavily_key) if tavily_key else _search_duckduckgo(attempt)
            except Exception as e:
                logger.warning(f"⚠️ Web search failed for '{attempt}': {e}")
                continue
            results = [r for r in results if r["url"]]
            if results:
                break

        if not results:
            return {"answer": "A busca na web falhou ou não retornou resultados. Responda com seu "
                              "conhecimento geral e avise o aluno que não foi possível consultar "
                              "fontes externas.", "sources": []}

        listing = "\n\n".join(
            f"[{i}] {r['title']}\nURL: {r['url']}\n{r['snippet']}" for i, r in enumerate(results, 1))
        answer = (
            "Resultados da web (NÃO são materiais do curso). Use apenas o que for confiável, "
            "prefira fontes científicas ou institucionais, e cite os links usados no bloco "
            "\"Informação complementar (fora do acervo)\".\n\n" + listing
        )
        sources = [{"title": r["title"], "source": r["url"], "chunk": r["snippet"][:300],
                    "page": None, "type": "web"} for r in results]
        return {"answer": answer, "sources": sources}

    async def _arun(self, query: str) -> Dict[str, Any]:
        return self._run(query)

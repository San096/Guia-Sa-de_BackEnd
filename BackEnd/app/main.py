from typing import Optional, List, Dict, Any, Tuple
import time
import re

import requests
from bs4 import BeautifulSoup
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

from app.data.sintomas import SINTOMAS
from app.data.orientacoes import ORIENTACOES

# ✅ Opcional: manter como fallback (recomendado)
# Se você NÃO quiser fallback, pode remover este import e as referências a FALLBACK_UNIDADES.
from app.data.unidades import UNIDADES as FALLBACK_UNIDADES


app = FastAPI(
    title="Guia Saúde API",
    version="1.0.0",
    description="API do trabalho final (FastAPI). Rotas GET em JSON para consumo via fetch no frontend.",
)

# ✅ CORS: libera seu front na Vercel
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://guia-saude-front-end.vercel.app"],
    allow_credentials=False,
    allow_methods=["GET", "OPTIONS"],
    allow_headers=["*"],
)

# -------------------------
# SCRAPING CONFIG
# -------------------------
LIST_URL = "https://quixada.ce.gov.br/unidadesaude.php"
DETAIL_URL = "https://quixada.ce.gov.br/unidadesaude.php?id={id}"
HEADERS = {"User-Agent": "GuiaSaude-Academico/1.0"}

# Cache em memória (pra não raspar toda hora)
CACHE_TTL_SECONDS = 6 * 60 * 60  # 6 horas (ajuste se quiser)
_unidades_cache: List[Dict[str, Any]] | None = None
_cache_ts: float = 0.0


def _fetch_soup(url: str) -> BeautifulSoup:
    r = requests.get(url, headers=HEADERS, timeout=25)
    r.raise_for_status()
    return BeautifulSoup(r.text, "lxml")


def _extract_first_text_after_label(soup: BeautifulSoup, label_regex: str) -> Optional[str]:
    """
    Heurística: acha uma seção pelo texto (ex: 'Informações de endereço')
    e retorna o primeiro texto relevante que aparecer depois.
    """
    node = soup.find(string=re.compile(label_regex, re.I))
    if not node:
        return None

    # tenta ler próximos textos “úteis”
    for el in node.parent.find_all_next(string=True):
        t = (el or "").strip()
        if not t:
            continue
        if re.search(label_regex, t, re.I):
            continue
        # evita pegar títulos de outras seções
        if re.search(r"(Profissionais|Serviços|Especialidades|Unidades|Contato)", t, re.I):
            break
        if len(t) >= 4:
            return re.sub(r"\s+", " ", t)
    return None


def _guess_nome(soup: BeautifulSoup) -> Optional[str]:
    for tag in ["h1", "h2", "h3"]:
        h = soup.find(tag)
        if h and h.get_text(strip=True):
            return h.get_text(" ", strip=True)
    return None


def _infer_tipo(nome: str, endereco: Optional[str], page_text: str) -> str:
    hay = " ".join([nome or "", endereco or "", page_text or ""]).upper()
    if "UPA" in hay:
        return "upa"
    if "HOSPITAL" in hay:
        return "hospital"
    # UBS / Posto / Unidade Básica
    if "UBS" in hay or "POSTO" in hay or "UNIDADE BASICA" in hay or "UNIDADE BÁSICA" in hay:
        return "ubs"
    return "ubs"


def _extract_bairro_from_endereco(endereco: Optional[str]) -> Optional[str]:
    """
    Heurística: muitos endereços vêm com ' - BAIRRO - '.
    Ex: 'RUA X, 123 - CENTRO - ... - QUIXADÁ'
    """
    if not endereco:
        return None
    parts = [p.strip() for p in endereco.split("-") if p.strip()]
    if len(parts) < 2:
        return None

    # normalmente o bairro é o segundo bloco
    cand = parts[1].title()

    # evita termos ruins
    bad = {"Zona Urbana", "Zona Rural", "Quixadá", "Ceará", "Ce", "Brasil"}
    if cand in bad and len(parts) >= 3:
        cand = parts[2].title()

    if len(cand) < 3:
        return None
    return cand


def _scrape_ids() -> List[int]:
    soup = _fetch_soup(LIST_URL)
    ids = set()

    for a in soup.select('a[href*="unidadesaude.php?id="]'):
        href = a.get("href", "")
        m = re.search(r"id=(\d+)", href)
        if m:
            ids.add(int(m.group(1)))

    return sorted(ids)


def _scrape_detail(unit_id: int) -> Dict[str, Any]:
    url = DETAIL_URL.format(id=unit_id)
    soup = _fetch_soup(url)

    nome = _guess_nome(soup) or f"Unidade {unit_id}"
    page_text = soup.get_text(" ", strip=True)

    endereco = _extract_first_text_after_label(soup, r"Informações de endereço")
    horario = _extract_first_text_after_label(soup, r"Horário de funcionamento")

    tipo = _infer_tipo(nome, endereco, page_text)
    bairro = _extract_bairro_from_endereco(endereco)

    return {
        "id": unit_id,
        "nome": nome,
        "tipo": tipo,           # ubs | upa | hospital
        "endereco": endereco,
        "bairro": bairro,
        "horario": horario,
        "telefone": None,
        "email": None,
        "fonteUrl": url,
    }


def get_unidades_scraped() -> List[Dict[str, Any]]:
    """
    Retorna unidades via scraping com cache (TTL).
    Se falhar, usa fallback (se existir).
    """
    global _unidades_cache, _cache_ts

    now = time.time()
    if _unidades_cache is not None and (now - _cache_ts) < CACHE_TTL_SECONDS:
        return _unidades_cache

    try:
        ids = _scrape_ids()
        unidades: List[Dict[str, Any]] = []

        # raspa cada detalhe (com pausa pequena pra não sobrecarregar)
        for i, uid in enumerate(ids, start=1):
            unidades.append(_scrape_detail(uid))
            time.sleep(0.35)

        _unidades_cache = unidades
        _cache_ts = now
        return unidades

    except Exception:
        # ✅ fallback (se você quiser 100% SEM fallback, remova isso e "raise")
        return FALLBACK_UNIDADES


@app.get("/")
def root():
    return {"message": "Guia Saúde API - online"}


@app.get("/api/health")
def health():
    return {"status": "ok"}


# Rota 1: sintomas
@app.get("/api/sintomas")
def listar_sintomas():
    return SINTOMAS


# Rota 2: orientações/regras
@app.get("/api/orientacoes")
def obter_orientacoes():
    return ORIENTACOES


# Rota 3: unidades (scraping + filtros)
@app.get("/api/unidades")
def listar_unidades(
    tipo: Optional[str] = Query(default=None, description="ubs | upa | hospital"),
    q: Optional[str] = Query(default=None, description="busca por nome/bairro/endereço"),
):
    results = get_unidades_scraped()

    if tipo:
        tipo_norm = tipo.strip().lower()
        results = [u for u in results if str(u.get("tipo", "")).lower() == tipo_norm]

    if q:
        q_norm = q.strip().lower()

        def haystack(u):
            return f"{u.get('nome','')} {u.get('bairro','')} {u.get('endereco','')}".lower()

        results = [u for u in results if q_norm in haystack(u)]

    return results

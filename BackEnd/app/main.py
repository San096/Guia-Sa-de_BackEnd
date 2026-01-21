from typing import Optional, List, Dict, Any
import time
import re

import requests
from bs4 import BeautifulSoup
from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.data.sintomas import SINTOMAS
from app.data.orientacoes import ORIENTACOES


app = FastAPI(
    title="Guia Saúde API",
    version="1.0.0",
    description="API do trabalho final (FastAPI). Dados em JSON para o frontend.",
)

# CORS – libera o frontend
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

CACHE_TTL_SECONDS = 6 * 60 * 60
_unidades_cache: List[Dict[str, Any]] | None = None
_cache_ts: float = 0.0


def _fetch_soup(url: str) -> BeautifulSoup:
    r = requests.get(url, headers=HEADERS, timeout=25)
    r.raise_for_status()
    return BeautifulSoup(r.text, "lxml")


def _extract_bairro_from_endereco(endereco: Optional[str]) -> Optional[str]:
    if not endereco:
        return None
    parts = [p.strip() for p in endereco.split("-") if p.strip()]
    if len(parts) < 2:
        return None
    cand = parts[1].title()
    if len(cand) < 3:
        return None
    return cand


def _infer_tipo(nome: str, endereco: Optional[str], page_text: str) -> str:
    hay = f"{nome} {endereco or ''} {page_text}".upper()

    if "CAPS" in hay:
        return "caps"
    if "UPA" in hay:
        return "upa"
    if "HOSPITAL" in hay:
        return "hospital"
    if "UBS" in hay or "POSTO" in hay or "UNIDADE BASICA" in hay or "UNIDADE BÁSICA" in hay:
        return "ubs"

    return "ubs"


def _scrape_list_unidades() -> List[Dict[str, Any]]:
    soup = _fetch_soup(LIST_URL)
    anchors = []

    for a in soup.select('a[href*="unidadesaude.php?id="]'):
        txt = a.get_text(" ", strip=True)
        if txt and txt.upper() != "VISUALIZAR":
            anchors.append(a)

    unidades = []

    for a in anchors:
        href = a.get("href", "")
        m = re.search(r"id=(\d+)", href)
        if not m:
            continue

        uid = int(m.group(1))
        nome = a.get_text(" ", strip=True)

        texts = []
        for el in a.next_elements:
            if getattr(el, "name", None) == "a":
                t = el.get_text(" ", strip=True)
                h = el.get("href", "")
                if t and t.upper() != "VISUALIZAR" and "unidadesaude.php?id=" in h:
                    break
            if isinstance(el, str):
                t = el.strip()
                if t:
                    texts.append(re.sub(r"\s+", " ", t))

        block = " ".join(texts)

        endereco = next((t for t in texts if "RUA" in t.upper()), None)
        horario = next((t for t in texts if "SEG" in t.upper() or "24" in t), None)
        email = next((t for t in texts if "@" in t), None)

        bairro = _extract_bairro_from_endereco(endereco)
        tipo = _infer_tipo(nome, endereco, block)

        unidades.append(
            {
                "id": uid,
                "nome": nome,
                "tipo": tipo,
                "endereco": endereco,
                "bairro": bairro,
                "horario": horario,
                "telefone": None,
                "email": email,
                "fonteUrl": DETAIL_URL.format(id=uid),
            }
        )

    return unidades


def get_unidades_scraped() -> List[Dict[str, Any]]:
    global _unidades_cache, _cache_ts

    now = time.time()
    if _unidades_cache and (now - _cache_ts) < CACHE_TTL_SECONDS:
        return _unidades_cache

    try:
        unidades = _scrape_list_unidades()
        if len(unidades) < 10:
            raise RuntimeError("Poucas unidades retornadas no scraping")

        _unidades_cache = unidades
        _cache_ts = now
        return unidades

    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Erro no scraping: {e}")


# -------------------------
# ROTAS
# -------------------------
@app.get("/")
def root():
    return {"message": "Guia Saúde API - online"}


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/sintomas")
def listar_sintomas():
    return SINTOMAS


@app.get("/api/orientacoes")
def obter_orientacoes():
    return ORIENTACOES


@app.get("/api/unidades")
def listar_unidades(
    tipo: Optional[str] = Query(default=None),
    q: Optional[str] = Query(default=None),
):
    results = get_unidades_scraped()

    if tipo:
        tipo_norm = tipo.lower()
        results = [u for u in results if u.get("tipo") == tipo_norm]

    if q:
        qn = q.lower()
        results = [
            u
            for u in results
            if qn in f"{u.get('nome','')} {u.get('bairro','')} {u.get('endereco','')}".lower()
        ]

    return results

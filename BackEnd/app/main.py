from typing import Optional

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

from app.data.sintomas import SINTOMAS
from app.data.orientacoes import ORIENTACOES
from app.data.unidades import UNIDADES

app = FastAPI(
    title="Guia Saúde API",
    version="1.0.0",
    description="API do trabalho final (FastAPI). Rotas GET em JSON para consumo via fetch no frontend.",
)

# ✅ CORS: libera seu front na Vercel
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://guia-saude-front-end.vercel.app",
     
    ],
    allow_credentials=False,
    allow_methods=["GET", "OPTIONS"],
    allow_headers=["*"],
)

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

# Rota 3: unidades (com filtros opcionais)
@app.get("/api/unidades")
def listar_unidades(
    tipo: Optional[str] = Query(default=None, description="ubs | upa | hospital"),
    q: Optional[str] = Query(default=None, description="busca por nome/bairro/endereço"),
):
    results = UNIDADES

    if tipo:
        tipo_norm = tipo.strip().lower()
        results = [u for u in results if str(u.get("tipo", "")).lower() == tipo_norm]

    if q:
        q_norm = q.strip().lower()

        def haystack(u):
            return f"{u.get('nome','')} {u.get('bairro','')} {u.get('endereco','')}".lower()

        results = [u for u in results if q_norm in haystack(u)]

    return results

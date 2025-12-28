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

# CORS: libera o frontend abrir a API no navegador
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # para trabalho acadêmico ok; em produção, restrinja
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
    tipo: str | None = Query(default=None, description="ubs | upa | hospital"),
    q: str | None = Query(default=None, description="busca por nome/bairro/endereço"),
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

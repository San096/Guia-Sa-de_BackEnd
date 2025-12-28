
---

## README — Backend (`backend/README.md`)

```md
# Backend — Guia Saúde (FastAPI)

Este é o backend do projeto **Guia Saúde**, desenvolvido com **FastAPI**.
Ele fornece dados em JSON para o frontend consumir via `fetch(GET)`.

## Requisitos
- Python 3.10+ (recomendado)
- pip

## Instalação
1. Entre na pasta do backend:
```bash
cd backend
python -m venv .venv


Windows (PowerShell):
.venv\Scripts\activate


 Linux/Mac:
python -m venv .venv
source .venv/bin/activate


Instale as dependências:
pip install -r requirements.txt


Como rodar a API.
Execute o servidor:
uvicorn app.main:app --reload --host 0.0.0.0 --port 3333

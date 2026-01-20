import re
import time
import json
import pprint
from pathlib import Path

import requests
from bs4 import BeautifulSoup

BASE = "https://quixada.ce.gov.br/unidadesaude.php"
UA = {"User-Agent": "GuiaSaude-Academic/1.0"}

# Vai sobrescrever este arquivo:
OUT_PY = Path(__file__).resolve().parents[1] / "app" / "data" / "unidades.py"


def fetch_html(url: str) -> BeautifulSoup:
    r = requests.get(url, headers=UA, timeout=20)
    r.raise_for_status()
    return BeautifulSoup(r.text, "lxml")


def scrape_ids() -> list[int]:
    soup = fetch_html(BASE)
    ids = set()

    for a in soup.select('a[href*="unidadesaude.php?id="]'):
        href = a.get("href", "")
        m = re.search(r"id=(\d+)", href)
        if m:
            ids.add(int(m.group(1)))

    return sorted(ids)


def pick_first_meaningful_text(soup: BeautifulSoup, label: str) -> str | None:
    """
    Procura um texto após um rótulo (ex: "Informações de endereço", "Horário de funcionamento").
    Como HTML pode variar, usamos uma heurística simples.
    """
    node = soup.find(string=re.compile(label, re.I))
    if not node:
        return None

    # Caminha adiante procurando um texto útil
    for el in node.parent.find_all_next(string=True):
        t = el.strip()
        if t and not re.search(label, t, re.I):
            # evita capturar títulos de seção
            if len(t) > 3:
                return re.sub(r"\s+", " ", t)
    return None


def guess_title(soup: BeautifulSoup) -> str | None:
    # tenta pegar o primeiro h1/h2/h3
    for tag in ["h1", "h2", "h3"]:
        h = soup.find(tag)
        if h and h.get_text(strip=True):
            return h.get_text(" ", strip=True)
    return None


def scrape_detail(unit_id: int) -> dict:
    url = f"{BASE}?id={unit_id}"
    soup = fetch_html(url)

    nome = guess_title(soup) or f"Unidade {unit_id}"
    endereco = pick_first_meaningful_text(soup, r"Informações de endereço")
    horario = pick_first_meaningful_text(soup, r"Horário de funcionamento")

    return {
        "id": unit_id,
        "nome": nome,
        "tipo": "ubs",  
        "endereco": endereco,
        "bairro": None,
        "horario": horario,
        "telefone": None,
        "email": None,
        "fonteUrl": url,
    }


def write_unidades_py(unidades: list[dict]):
    header = (
        "# Arquivo gerado automaticamente por scripts/scrape_unidades.py\n"
        "# Fonte: https://quixada.ce.gov.br/unidadesaude.php\n"
        "# Edite rodando o script novamente.\n\n"
    )
    # formata bonito como python
    body = "UNIDADES = " + pprint.pformat(unidades, width=110, sort_dicts=False) + "\n"

    OUT_PY.write_text(header + body, encoding="utf-8")
    print(f"✅ Gerado: {OUT_PY}")


def main():
    ids = scrape_ids()
    print(f"Encontrados {len(ids)} IDs.")

    unidades = []
    for i, unit_id in enumerate(ids, start=1):
        try:
            unidades.append(scrape_detail(unit_id))
            print(f"[{i}/{len(ids)}] OK id={unit_id}")
            time.sleep(0.5)  # seja educado com o servidor
        except Exception as e:
            print(f"[{i}/{len(ids)}] ERRO id={unit_id}: {e}")

    write_unidades_py(unidades)


if __name__ == "__main__":
    main()

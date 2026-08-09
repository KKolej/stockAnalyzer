#!/usr/bin/env python3
"""Podgląd i edycja tabeli `portfel` w n8n — pozycja po pozycji, z dyktanda.

Powstało dlatego, że pozycje podaje się w rozmowie („dokupiłem 10 CDR po 205"), a ręczne
sklejanie JSON-a z kwotami to najlepszy sposób, żeby pomylić się o rząd wielkości.
Skrypt czyta AKTUALNY stan z n8n, nanosi zmianę i odsyła pełną listę — nigdy nie zgaduje,
co jest w tabeli.

    python3 scripts/portfolio_edit.py show
    python3 scripts/portfolio_edit.py set CDR 40 198.50 --data 2026-05-12 --notatka "pod premierę"
    python3 scripts/portfolio_edit.py dokup CDR 10 205.00      # uśrednia z istniejącą pozycją
    python3 scripts/portfolio_edit.py rm PKO

Bez `--send` skrypt tylko pokazuje różnicę. Token: `PORTFEL_IMPORT_TOKEN` albo `--token`.
Notatki i tak są chronione po stronie webhooka, ale tutaj też są zachowywane wprost.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from typing import Any

BASE = os.environ.get("PORTFEL_URL_BASE", "https://fun-mouse9955.byst.re/webhook")
URL_STAN = f"{BASE}/portfel-stan"
URL_IMPORT = f"{BASE}/portfel-import"


def _zadanie(url: str, token: str, body: dict[str, Any] | None = None) -> dict[str, Any]:
    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8") if body is not None else None,
        headers={"Content-Type": "application/json", "X-Portfel-Token": token},
        method="POST" if body is not None else "GET",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read().decode("utf-8"))  # type: ignore[no-any-return]
    except urllib.error.HTTPError as e:
        sys.exit(f"n8n odrzucił żądanie ({e.code}): {e.read().decode('utf-8', 'replace')[:400]}")
    except urllib.error.URLError as e:
        sys.exit(f"Nie dodzwoniłem się do n8n: {e.reason}")


def pokaz(pozycje: list[dict[str, Any]], naglowek: str) -> None:
    print(f"\n{naglowek}")
    if not pozycje:
        print("  (pusto)")
        return
    print(f"  {'TICKER':10} {'SZTUK':>9} {'CENA':>11}  {'DATA':10}  NOTATKA")
    for p in sorted(pozycje, key=lambda x: str(x.get("ticker"))):
        print(
            f"  {str(p.get('ticker')):10} {float(p.get('szt', 0)):>9.4g} "
            f"{float(p.get('cena_kupna', 0)):>11.4f}  {str(p.get('data') or '—'):10}  {p.get('notatka') or ''}"
        )


def main() -> None:
    ap = argparse.ArgumentParser(description="Podgląd i edycja tabeli `portfel` w n8n")
    ap.add_argument("--token", default=os.environ.get("PORTFEL_IMPORT_TOKEN", ""))
    ap.add_argument("--send", action="store_true", help="zapisz zmianę (domyślnie tylko podgląd)")
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("show", help="pokaż aktualny portfel")

    p_set = sub.add_parser("set", help="ustaw pozycję (nadpisuje istniejącą)")
    p_set.add_argument("ticker")
    p_set.add_argument("szt", type=float)
    p_set.add_argument("cena", type=float)
    p_set.add_argument("--data", default="")
    p_set.add_argument("--notatka", default=None)

    p_add = sub.add_parser("dokup", help="dołóż do pozycji, uśredniając cenę")
    p_add.add_argument("ticker")
    p_add.add_argument("szt", type=float)
    p_add.add_argument("cena", type=float)
    p_add.add_argument("--notatka", default=None)

    p_rm = sub.add_parser("rm", help="usuń pozycję")
    p_rm.add_argument("ticker")

    args = ap.parse_args()
    if not args.token:
        sys.exit("Brak tokenu: ustaw PORTFEL_IMPORT_TOKEN albo podaj --token.")

    stan = _zadanie(URL_STAN, args.token)
    pozycje: list[dict[str, Any]] = list(stan.get("pozycje") or [])
    pokaz(pozycje, "PRZED:")

    if args.cmd == "show":
        return

    ticker = args.ticker.strip().upper()
    biezaca = next((p for p in pozycje if str(p.get("ticker", "")).upper() == ticker), None)
    inne = [p for p in pozycje if str(p.get("ticker", "")).upper() != ticker]

    if args.cmd == "rm":
        if not biezaca:
            sys.exit(f"{ticker} nie ma w portfelu — nic nie zmieniam.")
        nowe = inne
    elif args.cmd == "set":
        notatka = args.notatka if args.notatka is not None else (biezaca or {}).get("notatka", "")
        nowe = [*inne, {"ticker": ticker, "szt": args.szt, "cena_kupna": args.cena,
                        "data": args.data or (biezaca or {}).get("data", ""), "notatka": notatka or ""}]
    else:  # dokup
        stare_szt = float((biezaca or {}).get("szt", 0) or 0)
        stara_cena = float((biezaca or {}).get("cena_kupna", 0) or 0)
        laczne = stare_szt + args.szt
        # Średnia ważona — tabela trzyma jeden wiersz na spółkę, więc dokupienie musi
        # zmienić cenę wejścia, a nie tylko liczbę sztuk.
        cena = (stare_szt * stara_cena + args.szt * args.cena) / laczne if laczne else args.cena
        notatka = args.notatka if args.notatka is not None else (biezaca or {}).get("notatka", "")
        nowe = [*inne, {"ticker": ticker, "szt": round(laczne, 4), "cena_kupna": round(cena, 4),
                        "data": (biezaca or {}).get("data", ""), "notatka": notatka or ""}]

    pokaz(nowe, "PO:")

    if not args.send:
        print("\n(podgląd — dodaj --send, żeby zapisać)")
        return

    body: dict[str, Any] = {"pozycje": nowe}
    if not nowe:
        body["force"] = True          # świadome opróżnienie portfela
    odp = _zadanie(URL_IMPORT, args.token, body)
    print(f"\nZapisane: {odp.get('wierszy')} pozycji")
    if odp.get("zachowane_notatki"):
        print(f"Notatki zachowane: {', '.join(odp['zachowane_notatki'])}")


if __name__ == "__main__":
    main()

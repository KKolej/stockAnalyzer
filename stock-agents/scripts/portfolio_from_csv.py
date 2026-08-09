#!/usr/bin/env python3
"""Wgrywa pozycje z pliku CSV (eksport z xStation/innego brokera) do tabeli `portfel` w n8n.

Domyślnie tylko POKAZUJE, co zrobi — wysyłka wymaga `--send`. Notatki w tabeli zostają
nietknięte: webhook doklei je z powrotem po tickerze, bo CSV od brokera wie ile i po ile,
ale nie wie PO CO kupiłeś.

    python3 scripts/portfolio_from_csv.py pozycje.csv                 # podgląd
    python3 scripts/portfolio_from_csv.py pozycje.csv --send          # wgranie

Token: `PORTFEL_IMPORT_TOKEN` w środowisku albo `--token`. Leży w n8n →
Credentials → „Portfel import token".

Format pliku nie jest z góry ustalony — nagłówki są dopasowywane po nazwach (PL i EN),
separator i kodowanie wykrywane, przecinek dziesiętny obsłużony. Gdy plik ma inne
nagłówki, skrypt wypisze, co znalazł, zamiast zgadywać.
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import os
import sys
import urllib.error
import urllib.request
from collections import defaultdict
from typing import Any

DEFAULT_URL = "https://fun-mouse9955.byst.re/webhook/portfel-import"

# Nagłówki bywają po polsku albo angielsku, z ogonkami albo bez — dopasowanie jest
# po fragmencie nazwy, nie po równości.
KOLUMNY = {
    "symbol": ["symbol", "instrument", "walor", "ticker", "nazwa"],
    "volume": ["wolumen", "volume", "ilosc", "ilość", "liczba", "quantity", "szt"],
    "price": ["cena otwarcia", "open price", "openprice", "cena zakupu", "srednia cena",
              "średnia cena", "price", "cena"],
    "date": ["data otwarcia", "open time", "opentime", "data zakupu", "data", "date"],
    "side": ["typ", "kierunek", "type", "side", "cmd", "operacja"],
}

# GPW w XTB to `PKO.PL`; nasze tickery są bez sufiksu. `.US` zostawiamy, bo tak samo
# adresujemy rynki zagraniczne w API.
SUFIKSY_DO_USUNIECIA = (".PL", "_PL", ".WA")


def wczytaj(path: str) -> list[dict[str, str]]:
    with open(path, "rb") as fh:
        surowe = fh.read()
    for kodowanie in ("utf-8-sig", "cp1250", "utf-8", "latin-1"):
        try:
            tekst = surowe.decode(kodowanie)
            break
        except UnicodeDecodeError:
            continue
    else:
        sys.exit("Nie udało się odczytać pliku w żadnym ze znanych kodowań.")

    probka = tekst[:4096]
    try:
        dialekt = csv.Sniffer().sniff(probka, delimiters=";,\t|")
        sep = dialekt.delimiter
    except csv.Error:
        # Eksporty z polskich platform najczęściej używają średnika (przecinek jest
        # zajęty przez część dziesiętną).
        sep = ";" if probka.count(";") >= probka.count(",") else ","

    wiersze = list(csv.DictReader(io.StringIO(tekst), delimiter=sep))
    if not wiersze:
        sys.exit("Plik nie zawiera żadnych wierszy danych.")
    return wiersze


def dopasuj_kolumny(naglowki: list[str]) -> dict[str, str]:
    znalezione: dict[str, str] = {}
    for pole, warianty in KOLUMNY.items():
        for h in naglowki:
            czysty = (h or "").strip().lower()
            if any(w in czysty for w in warianty):
                znalezione[pole] = h
                break
    return znalezione


def liczba(tekst: str) -> float | None:
    t = (tekst or "").strip().replace("\xa0", "").replace(" ", "")
    if not t:
        return None
    # "1 234,56" i "1,234.56" znaczą to samo w różnych eksportach.
    if "," in t and "." in t:
        t = t.replace(".", "").replace(",", ".") if t.rfind(",") > t.rfind(".") else t.replace(",", "")
    else:
        t = t.replace(",", ".")
    try:
        return float(t)
    except ValueError:
        return None


def na_ticker(symbol: str) -> str:
    s = (symbol or "").strip().upper()
    for suf in SUFIKSY_DO_USUNIECIA:
        if s.endswith(suf):
            return s[: -len(suf)]
    return s


def main() -> None:
    ap = argparse.ArgumentParser(description="CSV z pozycjami -> tabela `portfel` w n8n")
    ap.add_argument("csv_path")
    ap.add_argument("--send", action="store_true", help="faktycznie wyślij (domyślnie tylko podgląd)")
    ap.add_argument("--url", default=os.environ.get("PORTFEL_IMPORT_URL", DEFAULT_URL))
    ap.add_argument("--token", default=os.environ.get("PORTFEL_IMPORT_TOKEN", ""))
    args = ap.parse_args()

    wiersze = wczytaj(args.csv_path)
    naglowki = list(wiersze[0].keys())
    kol = dopasuj_kolumny(naglowki)

    print(f"Kolumny w pliku: {', '.join(h for h in naglowki if h)}")
    print(f"Rozpoznane:      {json.dumps(kol, ensure_ascii=False)}\n")
    brakujace = [p for p in ("symbol", "volume", "price") if p not in kol]
    if brakujace:
        sys.exit(
            f"Nie rozpoznałem kolumn: {', '.join(brakujace)}.\n"
            "Dopisz nazwę nagłówka do KOLUMNY w tym skrypcie albo pokaż plik — nie zgaduję."
        )

    # Jedna spółka bywa kupowana w kilku transzach; tabela trzyma jeden wiersz na spółkę,
    # więc cena to ŚREDNIA WAŻONA wolumenem, a data to pierwszy zakup.
    zebrane: dict[str, dict[str, Any]] = defaultdict(lambda: {"szt": 0.0, "wartosc": 0.0, "data": ""})
    pominiete: list[str] = []
    for w in wiersze:
        ticker = na_ticker(w.get(kol["symbol"], ""))
        szt = liczba(w.get(kol["volume"], ""))
        cena = liczba(w.get(kol["price"], ""))
        if not ticker or szt is None or cena is None or szt <= 0 or cena <= 0:
            if any((w.get(h) or "").strip() for h in naglowki):
                pominiete.append(f"{ticker or '?'}: wolumen={w.get(kol['volume'])!r} cena={w.get(kol['price'])!r}")
            continue
        if "side" in kol:
            typ = (w.get(kol["side"]) or "").strip().lower()
            # Krótkie pozycje nie mieszczą się w modelu portfela (ujemna liczba sztuk),
            # więc lepiej je pokazać niż policzyć jako zwykły zakup.
            if typ.startswith("s") or "sprzeda" in typ or typ == "1":
                pominiete.append(f"{ticker}: pozycja krótka/sprzedaż ({typ}) — pomijam")
                continue
        poz = zebrane[ticker]
        poz["szt"] += szt
        poz["wartosc"] += szt * cena
        data = (w.get(kol.get("date", ""), "") or "").strip()[:10].replace("/", "-").replace(".", "-")
        if data and (not poz["data"] or data < poz["data"]):
            poz["data"] = data

    pozycje = [
        {"ticker": t, "szt": round(v["szt"], 4), "cena_kupna": round(v["wartosc"] / v["szt"], 4), "data": v["data"]}
        for t, v in sorted(zebrane.items())
    ]

    print(f"{'TICKER':10} {'SZTUK':>10} {'ŚR. CENA':>12}  DATA")
    for p in pozycje:
        print(f"{p['ticker']:10} {p['szt']:>10.4g} {p['cena_kupna']:>12.4f}  {p['data'] or '—'}")
    if pominiete:
        print("\nPominięte wiersze:")
        for x in pominiete:
            print(f"  - {x}")
    if not pozycje:
        sys.exit("\nZero pozycji do wgrania — nic nie wysyłam.")

    if not args.send:
        print("\n(podgląd — dodaj --send, żeby wgrać do tabeli)")
        return
    if not args.token:
        sys.exit("Brak tokenu: ustaw PORTFEL_IMPORT_TOKEN albo podaj --token.")

    req = urllib.request.Request(
        args.url,
        data=json.dumps({"pozycje": pozycje}).encode("utf-8"),
        headers={"Content-Type": "application/json", "X-Portfel-Token": args.token},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            odp = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        sys.exit(f"Webhook odrzucił żądanie ({e.code}): {e.read().decode('utf-8', 'replace')[:400]}")
    except urllib.error.URLError as e:
        sys.exit(f"Nie dodzwoniłem się do n8n: {e.reason}")

    print(f"\nWgrane: {odp.get('wierszy')} pozycji")
    if odp.get("zachowane_notatki"):
        print(f"Notatki zachowane dla: {', '.join(odp['zachowane_notatki'])}")
    if odp.get("nowe_pozycje"):
        print(f"Nowe w portfelu:       {', '.join(odp['nowe_pozycje'])}")
    if odp.get("znikniete_pozycje"):
        print(f"Zniknęły z portfela:   {', '.join(odp['znikniete_pozycje'])}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Sprawdza, czy socket xAPI XTB da się wykorzystać do pobrania otwartych pozycji.

Dlaczego to osobny skrypt, a nie od razu endpoint: `ws.xtb.com` (WebSocket) zwraca 404
i przez to uznaliśmy kiedyś, że XTB nie ma już API. Socket `xapi.xtb.com:5124/5112` stoi
i kończy handshake ważnym certyfikatem, ale bez danych konta nie da się sprawdzić, czy
`login` przechodzi — a od tego zależy, czy w ogóle warto pisać integrację.

Skrypt NIE handluje i nie wysyła żadnej komendy zmieniającej stan konta: loguje się,
pyta o otwarte pozycje i wylogowuje. Hasła nie wypisuje ani nie zapisuje.

Uruchomienie (dane z .env albo ze środowiska):

    XTB_USER_ID=12345678 XTB_PASSWORD='...' XTB_DEMO=1 python3 scripts/xtb_probe.py

`XTB_DEMO=1` (domyślnie) łączy się z kontem demo — zacznij od niego. Konto realne
wymaga `XTB_DEMO=0`; te same dane logowania pozwalają składać zlecenia, więc
traktuj je jak hasło do banku.
"""

from __future__ import annotations

import contextlib
import json
import os
import socket
import ssl
import sys
import time
from typing import Any, cast

HOST = "xapi.xtb.com"
PORT_DEMO = 5124
PORT_REAL = 5112
# xAPI limits commands to one per 200 ms; going faster gets the connection dropped.
MIN_INTERVAL_S = 0.25
TIMEOUT_S = 20


class XtbError(RuntimeError):
    pass


class XtbClient:
    """Minimalny klient xAPI: JSON po TLS, komunikaty rozdzielone dwoma znakami nowej linii."""

    def __init__(self, demo: bool = True) -> None:
        self.port = PORT_DEMO if demo else PORT_REAL
        self._last_call = 0.0
        ctx = ssl.create_default_context()
        raw = socket.create_connection((HOST, self.port), timeout=TIMEOUT_S)
        self.sock = ctx.wrap_socket(raw, server_hostname=HOST)
        self._buf = ""

    def call(self, command: str, arguments: dict[str, Any] | None = None) -> dict[str, Any]:
        wait = MIN_INTERVAL_S - (time.monotonic() - self._last_call)
        if wait > 0:
            time.sleep(wait)
        payload: dict[str, Any] = {"command": command}
        if arguments:
            payload["arguments"] = arguments
        self.sock.sendall((json.dumps(payload) + "\n\n").encode("utf-8"))
        self._last_call = time.monotonic()
        return self._read()

    def _read(self) -> dict[str, Any]:
        # The server may split one record across TCP reads, so the buffer is parsed
        # incrementally instead of assuming one recv() equals one message.
        deadline = time.monotonic() + TIMEOUT_S
        while time.monotonic() < deadline:
            if "\n\n" in self._buf:
                record, self._buf = self._buf.split("\n\n", 1)
                record = record.strip()
                if record:
                    return cast(dict[str, Any], json.loads(record))
                continue
            chunk = self.sock.recv(65536)
            if not chunk:
                raise XtbError("serwer zamknął połączenie bez odpowiedzi")
            self._buf += chunk.decode("utf-8", "replace")
            # Some deployments omit the trailing blank line on the last record.
            try:
                parsed = json.loads(self._buf.strip())
            except json.JSONDecodeError:
                continue
            self._buf = ""
            return cast(dict[str, Any], parsed)
        raise XtbError(f"brak odpowiedzi w {TIMEOUT_S}s")

    def close(self) -> None:
        with contextlib.suppress(Exception):
            self.call("logout")
        with contextlib.suppress(Exception):
            self.sock.close()


def _fail(msg: str) -> None:
    print(f"NIE DZIAŁA: {msg}")
    sys.exit(1)


def main() -> None:
    user_id = os.environ.get("XTB_USER_ID", "").strip()
    password = os.environ.get("XTB_PASSWORD", "")
    demo = os.environ.get("XTB_DEMO", "1").strip() not in {"0", "false", "no"}

    if not user_id or not password:
        _fail("brak XTB_USER_ID lub XTB_PASSWORD w środowisku")

    tryb = "DEMO" if demo else "REALNE"
    print(f"Łączę z {HOST}:{PORT_DEMO if demo else PORT_REAL} (konto {tryb}), user {user_id[:2]}***")

    try:
        client = XtbClient(demo=demo)
    except Exception as exc:  # noqa: BLE001 — diagnostyka ma pokazać każdy powód
        _fail(f"nie udało się połączyć: {exc}")

    try:
        res = client.call("login", {"userId": user_id, "password": password})
        if not res.get("status"):
            _fail(f"login odrzucony: {res.get('errorCode')} {res.get('errorDescr')}")
        print("login: OK\n")

        res = client.call("getTrades", {"openedOnly": True})
        if not res.get("status"):
            _fail(f"getTrades odrzucone: {res.get('errorCode')} {res.get('errorDescr')}")

        trades = res.get("returnData") or []
        print(f"otwartych pozycji: {len(trades)}")
        if trades:
            print(f"\npola jednej pozycji: {sorted(trades[0].keys())}\n")
            for t in trades:
                print(
                    f"  {str(t.get('symbol')):14} wolumen={t.get('volume')} "
                    f"cena_otwarcia={t.get('open_price')} typ={t.get('cmd')} "
                    f"otwarta={t.get('open_timeString')}"
                )
        else:
            print("(konto bez otwartych pozycji — na demo to normalne)")

        res = client.call("getMarginLevel")
        if res.get("status"):
            d = res.get("returnData") or {}
            print(f"\nstan konta: equity={d.get('equity')} {d.get('currency')} balance={d.get('balance')}")
    finally:
        client.close()

    print("\nDZIAŁA — socket xAPI odpowiada, integracja jest wykonalna.")


if __name__ == "__main__":
    main()

# Agent backtest — wiarygodność sygnałów

`GET /backtest/{ticker}?years=5`

Odpowiada na jedno pytanie: **którym sygnałom ufać na TEJ spółce**. Dla każdej reguły
(RSI pod 30, przecięcie MACD, nowe maksimum 52W…) sprawdza, co działo się potem na
historii tej spółki, i zwraca liczby razem z próbą oraz testem istotności.

To **nie jest predyktor ceny**. Odpowiada „co się działo po tym sygnale", nigdy
„ile będzie kosztować w piątek".

## Dlaczego to jest najważniejszy agent dla jakości

Pozostali agenci mówią LLM-owi „RSI 28, wyprzedanie" — i model traktuje to tak samo
poważnie jak każdy inny sygnał. Ten agent dokłada: *na tej spółce to zdarzenie 22 razy
w 7 lat nie dało nic ponad zwykły ruch*. Dopiero wtedy model może ważyć sygnały, zamiast
je wyliczać. `speculator` wystawia `projections` z `is_backtested: false`; tutaj jest
`is_backtested: true` i to nie jest ozdobnik — te liczby są zmierzone.

## Trzy decyzje, które decydują o wiarygodności

**1. Wszystko liczone WZGLĘDEM BAZY.** „58% trafień" brzmi jak przewaga, dopóki nie
zobaczysz, że spółka rosła w 57% wszystkich okien tej długości. Raportowana jest różnica
wobec trzymania (`excess_return_pct`, `edge_pp`), nie liczba bezwzględna.

**2. Nakładające się okna są dyskontowane — przez liczenie, nie dzielenie.** Zdarzenia
trzy dni po sobie dzielą prawie to samo okno 21-dniowe. `effective_sample` to największy
podzbiór zdarzeń oddalonych o co najmniej `horizon` sesji. Pierwsza wersja dzieliła
`n / horizon` i to był błąd w drugą stronę: 22 przecięcia RSI rozrzucone po siedmiu latach
**są** niezależne, a dzielenie sprowadzało je do jednego.

**3. Za mała próba = brak werdyktu.** Poniżej 20 zdarzeń zwracamy „za mało danych", nie
procent. Osobno rozróżniamy „policzone, wyszło zero" od „nie dało się policzyć istotności"
(za mało niezależnych okien) — to nie to samo i mylenie tego wprowadza w błąd.

## Co warto wiedzieć o wynikach

- **Zero istotnych sygnałów to normalny i uczciwy wynik.** Na CDR, ALE i PZU (14 lat
  historii) nie wyszło nic. Na PKO wyszedł jeden: RSI > 70 → −1,52% w 10 sesji ponad bazę
  (n=68, t=−2,43).
- **Sygnał potrafi działać ODWROTNIE do podręcznika** i wtedy jest to napisane wprost.
  Na ART zejście pod dolną wstęgę Bollingera (podręcznikowo byczy sygnał kontry) dawało
  −5,62% w 21 sesji (n=72, t=−3,28) — czyli była to kontynuacja spadku, nie okazja.
- **Testujemy 12 sygnałów × 4 horyzonty = 48 kombinacji.** Przy tylu testach część wyników
  „istotnych" to przypadek — dlatego `caveats` mówi o tym wprost, a ranking sortuje po sile
  zmierzonej przewagi, nie po tym, jak sygnał jest opisany w podręczniku.

## Pola, które są tu najważniejsze

| Pole | Znaczenie |
|---|---|
| `excess_return_pct` | średni zwrot **ponad** to, co dało samo trzymanie w tym okresie |
| `edge_pp` | trafność minus trafność bazowa, w punktach procentowych |
| `sample_size` / `effective_sample` | ile zdarzeń / ile z nich niezależnych |
| `t_stat` | liczone na próbie efektywnej; `null` = nie dało się ocenić |
| `reliable` | próba ≥ 20 **i** \|t\| ≥ 2 |
| `reading` | jednozdaniowe odczytanie po polsku, łącznie z „DZIAŁAŁ ODWROTNIE" |
| `active_signals` | sygnały, które padły w ostatnich 5 sesjach — z ich historią |

`active_signals` to sklejka backtestu z dniem dzisiejszym: nie trzeba przekopywać tabeli,
żeby zobaczyć, czy dzisiejszy sygnał w ogóle się kiedyś sprawdzał.

## Czego tu NIE ma (świadomie)

- Kosztów transakcyjnych, podatku i poślizgu — zwroty są brutto.
- Walidacji na innych spółkach: wynik dotyczy jednej spółki i jednego okresu.
- Uczenia maszynowego. Gdyby kiedyś dokładać model, to dopiero po tym module i z tą samą
  dyscypliną: porównanie z bazą, walk-forward i odmowa werdyktu przy małej próbie.

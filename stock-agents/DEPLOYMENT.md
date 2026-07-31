# Wdrożenie: stock-agents + n8n na Mikrus (tani VPS)

Cel: `stock-api` + `n8n` chodzą 24/7 na tanim VPS. n8n co rano odpytuje endpointy,
przepuszcza dane przez Claude i wysyła maila, jeśli coś jest warte uwagi.

## 0. Jaki plan Mikrusa?

- **Wymagany Docker** → na Mikrusie Docker działa od planu **Mikrus 2.1 wzwyż**
  (frog/1.0 odpadają). Realne zużycie RAM: n8n ~400–600 MB, stock-api ~250–400 MB
  (pandas), więc celuj w plan z **≥ 2 GB RAM** (Mikrus 3.0). Na 2.1 też ruszy,
  ale dodaj swap (patrz niżej).
- Mikrus daje **współdzielone IPv4** — masz przydzielone **2 porty TCP**
  (widoczne w panelu mikr.us, np. `20123` i `30123`) + pełne IPv6.
  Nie możesz wystawić usługi na porcie 80/443 na IPv4 — używasz przydzielonych portów.
- Sprawdź w panelu Mikrusa aktualne opcje subdomen/HTTPS (panel → sekcja domen) —
  Mikrus oferuje darmowe subdomeny z proxy; szczegóły zmieniają się, więc
  traktuj panel jako źródło prawdy.

## 1. Przygotowanie serwera

```bash
ssh root@twojserwer.mikr.us -p PORT_SSH   # dane z panelu

# swap (ważne przy < 2GB RAM)
fallocate -l 1G /swapfile && chmod 600 /swapfile && mkswap /swapfile && swapon /swapfile
echo '/swapfile none swap sw 0 0' >> /etc/fstab

# docker (jeśli brak; na niektórych obrazach Mikrusa jest preinstalowany)
curl -fsSL https://get.docker.com | sh
```

## 2. Deploy aplikacji

```bash
git clone <URL_REPO> stock-agents && cd stock-agents

cat > .env <<'EOF'
# --- stock-api ---
API_BIND=127.0.0.1        # API niepubliczne; n8n dobija się po sieci compose
API_PORT=8000
CACHE_TTL=900

# --- n8n (USTAWIENIA PRODUKCYJNE) ---
N8N_PORT=20123            # <- TWÓJ przydzielony port z panelu Mikrusa!
N8N_USER_MANAGEMENT_DISABLED=false   # WYMAGANE na publicznym VPS — logowanie włączone
N8N_SECURE_COOKIE=false              # zostaw false, jeśli wchodzisz po http://IP:port
# N8N_WEBHOOK_URL=https://twoja-subdomena...   # jeśli używasz proxy/subdomeny Mikrusa
EOF

docker compose up -d --build
docker compose ps          # oba serwisy "healthy"/"running"
curl -s localhost:8000/health   # {"status":"ok"}
```

n8n dostępne pod: `http://<host-mikrusa>:<N8N_PORT>` (albo przez subdomenę z panelu).
Przy pierwszym wejściu n8n każe założyć konto właściciela — **zrób to od razu**,
bo instancja jest widoczna z internetu.

**Bezpieczeństwo — minimum:**
1. `N8N_USER_MANAGEMENT_DISABLED=false` (logowanie!) — inaczej każdy w internecie
   ma dostęp do Twoich workflow i credentiali.
2. `API_BIND=127.0.0.1` — stock-api nie wystawione publicznie (n8n i tak łączy się
   wewnętrznie po `http://stock-api:8000`).
3. Aktualizacje: `docker compose pull && docker compose up -d` co jakiś czas.

## 3. Workflow n8n: codzienny mail z analizą

Workflow z `n8n/stock-analysis-workflow.json` jest chatowy (ręczny). Do automatu
przerabiasz go tak:

```
Schedule Trigger (np. pn–pt 8:00)
   └─> HTTP Request: GET http://stock-api:8000/macro
   └─> HTTP Request: GET http://stock-api:8000/technical/PKO   (po jednym na ticker,
   └─> HTTP Request: GET http://stock-api:8000/fundamental/PKO  albo pętla po liście
   └─> HTTP Request: GET http://stock-api:8000/sentiment/PKO    tickerów z węzła Code)
        └─> Merge (złącz wszystkie odpowiedzi)
             └─> LLM (Claude — patrz sekcja 4)
                  prompt: "Przeanalizuj dane. Jeśli jest coś wartego uwagi
                  (mocne sygnały, okazje, ryzyka), opisz to po polsku i zacznij
                  odpowiedź od ALERT. Jeśli nic istotnego — odpowiedz NIC."
                  └─> IF (odpowiedź zaczyna się od "ALERT")
                       └─> Gmail / Send Email → mail do Ciebie
```

Praktyczne uwagi:
- W węzłach HTTP Request ustaw **timeout 60–120 s** (yfinance + scraping bywają wolne;
  drugi request w oknie cache'a (15 min) jest już szybki).
- Węzeł **Gmail** wymaga credentiala Google OAuth2 (w n8n: Credentials → Gmail).
  Prostsza alternatywa: węzeł **Send Email** (SMTP) z hasłem aplikacji Gmail.
- Zacznij od 3–5 tickerów; endpoint `/screener` może służyć do preselekcji.

## 4. Podpięcie Claude w n8n — 2 realne opcje

### Ważne wyjaśnienie na start

**Nie da się podpiąć n8n "bezpośrednio do czatu claude.ai"** (tego z przeglądarki).
Czat claude.ai nie ma API, a automatyzowanie go (headless browser, scraping sesji)
łamie warunki użytkowania Anthropic — nie rób tego. Realne opcje są dwie:

### Opcja A: API Anthropic (najprostsza) — koszt realnie **grosze**

Obawa o "dodatkowe tokeny" jest przy tym wolumenie nieuzasadniona. Policzmy:
1 mail dziennie, ~20–40 tys. tokenów wejścia (JSON-y z endpointów) + ~1 tys. wyjścia.

| Model | Cena (wej./wyj. za 1M tokenów) | Koszt dzienny | Koszt miesięczny |
|---|---|---|---|
| `claude-haiku-4-5` | $1 / $5 | ~$0.03–0.05 | **~1–1.5 USD** |
| `claude-sonnet-4-6` | $3 / $15 | ~$0.10–0.15 | ~3–4 USD |
| `claude-opus-5` | $5 / $25 | ~$0.17–0.25 | ~5–8 USD |

Do dziennego podsumowania sygnałów **Haiku 4.5 wystarcza** (dane i tak liczy
stock-api; LLM tylko syntetyzuje). Jak chcesz lepszą jakość wniosków — Sonnet.

Konfiguracja: [console.anthropic.com](https://console.anthropic.com) → API key →
w n8n Credentials → Anthropic → wklej klucz → w węźle AI Agent / Anthropic Chat Model
wybierz model. Doładuj $5 i wystarczy na miesiące.

### Opcja B: subskrypcja Claude (Pro/Max) przez Claude Code CLI — bez płacenia za tokeny

Jeśli masz **subskrypcję Claude Pro/Max**, możesz legalnie używać jej na serwerze
przez **Claude Code CLI** w trybie headless — to oficjalnie wspierana ścieżka
(limity zużycia = limity Twojej subskrypcji, bez rozliczania per token).

```bash
# na VPS (poza dockerem najprościej):
curl -fsSL https://claude.ai/install.sh | bash

# NA SWOIM KOMPUTERZE wygeneruj token subskrypcyjny (otwiera przeglądarkę):
claude setup-token
# → dostajesz długożyciowy token OAuth; na VPS ustaw:
export CLAUDE_CODE_OAUTH_TOKEN=sk-ant-oat01-...

# test headless:
claude -p "Odpowiedz jednym słowem: działa?"
```

W n8n używasz węzła **Execute Command** zamiast węzła Anthropic:

```bash
echo '{{ $json.dane_z_endpointow }}' | claude -p "Przeanalizuj te dane giełdowe... " --output-format text
```

Haczyki:
- n8n działa w kontenerze, a CLI jest na hoście → najprościej: węzeł **SSH**
  (n8n łączy się na `host` po SSH i odpala `claude -p ...`), albo zbuduj własny
  obraz n8n z doinstalowanym `@anthropic-ai/claude-code` i przekaż
  `CLAUDE_CODE_OAUTH_TOKEN` w environment.
- Limity subskrypcji są okienkowe (5h) — dla 1–2 uruchomień dziennie bez znaczenia.
- Token traktuj jak hasło (daje dostęp do Twojej subskrypcji).

### Rekomendacja

Na start **opcja A z Haiku 4.5** — 10 minut konfiguracji, ~1 USD/mies., zero haczyków
z kontenerami. Opcję B wybierz, gdy masz już Pro/Max i nie chcesz drugiego rozliczenia.

## 5. Utrzymanie

```bash
docker compose logs -f stock-api      # logi API
docker compose logs -f n8n            # logi n8n
docker compose restart                # restart
git pull && docker compose up -d --build   # aktualizacja aplikacji
```

Dane n8n (workflow, credentiale) żyją w wolumenie `n8n_data` — przeżywają
restart i rebuild. Backup: `docker run --rm -v stock-agents_n8n_data:/data -v $PWD:/backup alpine tar czf /backup/n8n-backup.tgz /data`.

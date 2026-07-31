from __future__ import annotations

import contextlib
import math
import re
import urllib.request
from datetime import date, timedelta

import pandas as pd
import yfinance as yf

from ...ticker_map import is_gpw
from .gaming_events import gaming_event_catalysts, is_gaming_company
from .models import Catalyst, PatternResult

_MIN_SAMPLE = 3

# Mapy sektorów GPW dostępnych w yfinance
_SECTOR_MAP: dict[str, str] = {
    "PKO": "WIG-BANKI.WA", "MBK": "WIG-BANKI.WA", "PZU": "WIG-BANKI.WA",
    "ALR": "WIG-BANKI.WA", "BNP": "WIG-BANKI.WA",
    "PKN": "WIG-PALIWA.WA", "MOL": "WIG-PALIWA.WA",
    "KGHM": "WIG-CHEMIA.WA",
    "LPP": "WIG-ODZIEZ.WA", "CCC": "WIG-ODZIEZ.WA",
    "CDR": "WIG-INFO.WA", "ATC": "WIG-INFO.WA",
    "BDX": "WIG-BUDOW.WA", "ENG": "WIG-BUDOW.WA",
    "OPL": "WIG-INFO.WA",
    "ALE": "WIG-SPOZYW.WA",
    "DNP": "WIG-SPOZYW.WA",
}
_BR_HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120 Safari/537.36",
}


def _price_return(df: pd.DataFrame, ref_date: date, offset_start: int, offset_end: int) -> float | None:
    start = ref_date + timedelta(days=offset_start)
    end = ref_date + timedelta(days=offset_end)
    mask = (df["Date"] >= pd.Timestamp(start)) & (df["Date"] <= pd.Timestamp(end))
    window = df[mask]
    if len(window) < 2:
        return None
    p_start = window.iloc[0]["Close"]
    p_end = window.iloc[-1]["Close"]
    if p_start == 0:
        return None
    return (p_end - p_start) / p_start


def _fetch_price_history(yahoo_ticker: str, years: int = 8) -> pd.DataFrame:
    raw = yf.download(yahoo_ticker, period=f"{years * 365}d", interval="1d",
                      auto_adjust=True, progress=False)
    if raw.empty:
        return pd.DataFrame()
    if isinstance(raw.columns, pd.MultiIndex):
        raw.columns = raw.columns.get_level_values(0)
    df = raw.reset_index()
    date_col = next((c for c in df.columns if str(c).lower() in ("date", "datetime")), df.columns[0])
    df = df.rename(columns={date_col: "Date"})
    df["Date"] = pd.to_datetime(df["Date"]).dt.tz_localize(None)
    return df[["Date", "Close", "Volume"]].dropna()


def _fetch_benchmark(ticker: str, years: int = 8) -> pd.DataFrame:
    bench = "WIG20.WA" if is_gpw(ticker) else "^GSPC"
    return _fetch_price_history(bench, years)


# ── Wzorzec dywidendowy ──────────────────────────────────────────────────────

def analyze_dividend_pattern(df: pd.DataFrame, div_dates: list[date]) -> list[PatternResult]:
    results = []
    pre_returns, post_returns = [], []

    for d in div_dates:
        pre = _price_return(df, d, -35, -2)
        post = _price_return(df, d, 1, 31)
        if pre is not None:
            pre_returns.append(pre)
        if post is not None:
            post_returns.append(post)

    if len(pre_returns) >= _MIN_SAMPLE:
        positive = sum(1 for r in pre_returns if r > 0)
        prob = positive / len(pre_returns)
        avg = sum(pre_returns) / len(pre_returns)
        direction = "UP" if prob >= 0.5 else "DOWN"
        prob_dir = prob if direction == "UP" else 1 - prob
        strength = "strong" if prob_dir >= 0.75 else "medium" if prob_dir >= 0.6 else "weak"
        trend = "rośnie" if direction == "UP" else "spada"
        results.append(PatternResult(
            name="Pre-div rally",
            direction=direction, strength=strength, probability=prob_dir,
            sample_size=len(pre_returns), avg_return=avg, horizon_days=30,
            note=(f"Przed ex-div {trend} w {max(positive, len(pre_returns)-positive)}"
                  f"/{len(pre_returns)} przypadkach (avg {avg*100:+.1f}%)"),
        ))

    if len(post_returns) >= _MIN_SAMPLE:
        negative = sum(1 for r in post_returns if r < 0)
        prob_drop = negative / len(post_returns)
        avg = sum(post_returns) / len(post_returns)
        direction = "DOWN" if prob_drop >= 0.5 else "UP"
        prob_dir = prob_drop if direction == "DOWN" else 1 - prob_drop
        strength = "strong" if prob_dir >= 0.75 else "medium" if prob_dir >= 0.6 else "weak"
        trend = "spada" if direction == "DOWN" else "rośnie"
        results.append(PatternResult(
            name="Post-div",
            direction=direction, strength=strength, probability=prob_dir,
            sample_size=len(post_returns), avg_return=avg, horizon_days=30,
            note=(f"Po ex-div {trend} w {max(negative, len(post_returns)-negative)}"
                  f"/{len(post_returns)} przypadkach (avg {avg*100:+.1f}%)"),
        ))

    return results


# ── Wzorzec wynikowy ─────────────────────────────────────────────────────────

def analyze_earnings_pattern(df: pd.DataFrame, earnings: pd.DataFrame) -> list[PatternResult]:
    results = []
    pre_returns, surprises = [], []

    for dt_idx in earnings.index:
        try:
            earn_date = dt_idx.date() if hasattr(dt_idx, "date") else dt_idx
        except Exception:
            continue

        pre = _price_return(df, earn_date, -12, -1)
        if pre is not None:
            pre_returns.append(pre)

        surprise = earnings.loc[dt_idx, "Surprise(%)"] if "Surprise(%)" in earnings.columns else None
        if surprise is not None and not (isinstance(surprise, float) and math.isnan(surprise)):
            surprises.append(float(surprise))

    if len(pre_returns) >= _MIN_SAMPLE:
        positive = sum(1 for r in pre_returns if r > 0)
        prob = positive / len(pre_returns)
        avg = sum(pre_returns) / len(pre_returns)
        direction = "UP" if prob >= 0.5 else "DOWN"
        prob_dir = prob if direction == "UP" else 1 - prob
        strength = "strong" if prob_dir >= 0.75 else "medium" if prob_dir >= 0.6 else "weak"
        trend = "rośnie" if direction == "UP" else "spada"
        results.append(PatternResult(
            name="Pre-earnings drift",
            direction=direction, strength=strength, probability=prob_dir,
            sample_size=len(pre_returns), avg_return=avg, horizon_days=12,
            note=(f"Przed raportem {trend} w {max(positive, len(pre_returns)-positive)}"
                  f"/{len(pre_returns)} przypadkach (avg {avg*100:+.1f}%)"),
        ))

    # Batting average — ważone magnitudą niespodzianki, nie tylko licznikiem
    if len(surprises) >= _MIN_SAMPLE:
        recent = surprises[:8]  # ostatnie 8 raportów ważniejsze
        avg_surprise = sum(surprises) / len(surprises)
        avg_recent = sum(recent) / len(recent)
        beats = sum(1 for s in surprises if s > 0)
        beat_pct = beats / len(surprises)

        # Kierunek oparty na średniej niespodziance (nie tylko na liczniku beatów)
        direction = "UP" if avg_surprise > 0 else "DOWN"
        # Siła = kombinacja beat% i magnitudy
        confidence = (beat_pct * 0.5 + (0.5 if avg_surprise > 0 else 0)) * min(abs(avg_surprise) / 10 + 0.5, 1.0)
        prob_dir = min(max(confidence, 0.4), 0.8)
        strength = "strong" if prob_dir >= 0.7 else "medium" if prob_dir >= 0.6 else "weak"

        results.append(PatternResult(
            name="Batting average",
            direction=direction, strength=strength, probability=prob_dir,
            sample_size=len(surprises), avg_return=None, horizon_days=5,
            note=(f"Bije EPS w {beats}/{len(surprises)} raportach, "
                  f"avg niespodzianka {avg_surprise:+.1f}% (ostatnie 8: {avg_recent:+.1f}%)"),
        ))

    return results


# ── Wolumen ──────────────────────────────────────────────────────────────────

def analyze_volume(df: pd.DataFrame) -> PatternResult | None:
    if len(df) < 25:
        return None
    recent_vol = df["Volume"].iloc[-1]
    avg_vol = df["Volume"].iloc[-21:-1].mean()
    if avg_vol == 0:
        return None
    ratio = recent_vol / avg_vol
    if ratio < 1.3:
        return None
    price_up = df["Close"].iloc[-1] > df["Close"].iloc[-2]
    direction = "UP" if price_up else "DOWN"
    strength = "strong" if ratio >= 2.5 else "medium" if ratio >= 1.8 else "weak"
    action = "akumulacja" if price_up else "dystrybucja"
    return PatternResult(
        name="Anomalia wolumenu",
        direction=direction, strength=strength,
        probability=0.65 if strength == "strong" else 0.55,
        sample_size=1, avg_return=None, horizon_days=7,
        note=f"Wolumen {ratio:.1f}x powyżej średniej — {action}",
    )


# ── Pozycja 52W ──────────────────────────────────────────────────────────────

def analyze_52w_position(df: pd.DataFrame) -> PatternResult | None:
    if len(df) < 50:
        return None
    year_data = df.tail(252)
    high = year_data["Close"].max()
    low = year_data["Close"].min()
    current = df["Close"].iloc[-1]
    if high == low:
        return None
    pos = (current - low) / (high - low)  # 0 = dno, 1 = szczyt

    if pos >= 0.9:
        return PatternResult(
            name="Pozycja 52W",
            direction="UP", strength="medium", probability=0.65,
            sample_size=252, avg_return=None, horizon_days=30,
            note=f"Blisko 52W szczytu ({pos*100:.0f}% zakresu) — momentum breakout",
        )
    if pos <= 0.15:
        return PatternResult(
            name="Pozycja 52W",
            direction="UP", strength="weak", probability=0.58,
            sample_size=252, avg_return=None, horizon_days=30,
            note=f"Blisko 52W dna ({pos*100:.0f}% zakresu) — potencjalne odbicie",
        )
    return None


# ── Momentum względne ────────────────────────────────────────────────────────

def _relative_momentum(df: pd.DataFrame, ref: pd.DataFrame, days: int, label: str) -> PatternResult | None:
    if len(df) < days + 1 or len(ref) < days + 1:
        return None
    merged = pd.merge(
        df[["Date", "Close"]].tail(days + 10),
        ref[["Date", "Close"]].tail(days + 10),
        on="Date", suffixes=("_s", "_b"),
    ).tail(days + 1)
    if len(merged) < days + 1:
        return None
    ret_stock = (merged["Close_s"].iloc[-1] - merged["Close_s"].iloc[0]) / merged["Close_s"].iloc[0]
    ret_bench = (merged["Close_b"].iloc[-1] - merged["Close_b"].iloc[0]) / merged["Close_b"].iloc[0]
    rel = ret_stock - ret_bench
    if abs(rel) < 0.02:
        return None
    direction = "UP" if rel > 0 else "DOWN"
    strength = "strong" if abs(rel) >= 0.05 else "medium" if abs(rel) >= 0.03 else "weak"
    sign = "+" if rel >= 0 else ""
    return PatternResult(
        name=f"Momentum vs {label} ({days}D)",
        direction=direction, strength=strength, probability=0.60,
        sample_size=days, avg_return=rel, horizon_days=days,
        note=f"Spółka {sign}{rel*100:.1f}% vs {label} — {'outperforms' if rel > 0 else 'underperforms'}",
    )


def analyze_momentum(df: pd.DataFrame, benchmark: pd.DataFrame,
                     sector: pd.DataFrame | None, sector_name: str,
                     bench_label: str = "WIG20") -> list[PatternResult]:
    results = []
    for days in (5, 20):
        p = _relative_momentum(df, benchmark, days, bench_label)
        if p:
            results.append(p)
    if sector is not None and not sector.empty:
        p = _relative_momentum(df, sector, 20, sector_name)
        if p:
            results.append(p)
    return results


# ── Sezonowość ───────────────────────────────────────────────────────────────

def analyze_seasonality(df: pd.DataFrame) -> PatternResult | None:
    if len(df) < 200:
        return None
    current_month = date.today().month
    df = df.copy()
    df["month"] = df["Date"].dt.month
    df["year"] = df["Date"].dt.year

    monthly_returns = []
    for year in df["year"].unique():
        yr = df[df["year"] == year]
        m = yr[yr["month"] == current_month]
        if len(m) < 2:
            continue
        ret = (m["Close"].iloc[-1] - m["Close"].iloc[0]) / m["Close"].iloc[0]
        monthly_returns.append(ret)

    if len(monthly_returns) < _MIN_SAMPLE:
        return None

    positive = sum(1 for r in monthly_returns if r > 0)
    prob = positive / len(monthly_returns)
    avg = sum(monthly_returns) / len(monthly_returns)

    if abs(prob - 0.5) < 0.15:
        return None

    direction = "UP" if prob >= 0.5 else "DOWN"
    strength = "medium" if prob >= 0.7 or prob <= 0.3 else "weak"
    mn = ["", "sty", "lut", "mar", "kwi", "maj", "cze",
          "lip", "sie", "wrz", "paź", "lis", "gru"][current_month]
    return PatternResult(
        name=f"Sezonowość ({mn})",
        direction=direction, strength=strength, probability=prob,
        sample_size=len(monthly_returns), avg_return=avg, horizon_days=30,
        note=f"{mn.capitalize()} historycznie up w {positive}/{len(monthly_returns)} latach (avg {avg*100:+.1f}%)",
    )


# ── Rekomendacje analityków (Biznesradar) ────────────────────────────────────

def analyze_analyst_recommendations(ticker: str) -> PatternResult | None:
    try:
        from bs4 import BeautifulSoup
        url = f"https://www.biznesradar.pl/rekomendacje-spolki/{ticker.upper()}"
        req = urllib.request.Request(url, headers=_BR_HEADERS)
        with urllib.request.urlopen(req, timeout=8) as r:
            soup = BeautifulSoup(r.read(), "lxml")

        table = soup.find("table")
        if not table:
            return None

        buys, holds, sells, targets = 0, 0, 0, []
        for row in table.find_all("tr")[1:8]:  # ostatnie ~6 rekomendacji
            cells = [td.get_text(strip=True) for td in row.find_all(["td", "th"])]
            if len(cells) < 4:
                continue
            rec_type = cells[0].lower()
            target_raw = cells[1]
            if "kupuj" in rec_type or "buy" in rec_type or "akumuluj" in rec_type:
                buys += 1
            elif "sprzedaj" in rec_type or "sell" in rec_type or "redukuj" in rec_type:
                sells += 1
            else:
                holds += 1
            # Parsuj cenę docelową
            m = re.search(r"[\d,\.]+", target_raw.replace(" ", "").replace("\xa0", ""))
            if m:
                with contextlib.suppress(ValueError):
                    targets.append(float(m.group().replace(",", ".")))

        total = buys + holds + sells
        if total == 0:
            return None

        direction = "UP" if buys > sells else "DOWN" if sells > buys else "NEUTRAL"
        raw_prob = buys / total if direction == "UP" else sells / total if direction == "DOWN" else 0.5
        # Small-sample discount: przy małej liczbie rekomendacji ograniczamy pewność
        confidence_cap = 0.5 + (raw_prob - 0.5) * min(total / 6, 1.0)
        prob = min(confidence_cap, 0.80)
        strength = "strong" if prob >= 0.72 else "medium" if prob >= 0.62 else "weak"

        avg_target = sum(targets) / len(targets) if targets else None
        target_str = f", cel avg {avg_target:.2f}" if avg_target else ""
        return PatternResult(
            name="Rekomendacje analityków",
            direction=direction, strength=strength, probability=prob,
            sample_size=total, avg_return=None, horizon_days=60,
            note=f"Kupuj:{buys} Trzymaj:{holds} Sprzedaj:{sells}{target_str}",
        )
    except Exception:
        return None


# ── Transakcje insiderów (Bankier) ───────────────────────────────────────────

# Mapowanie ticker → fragment nazwy w tabeli Bankier (uppercase)
_BANKIER_NAME_MAP: dict[str, list[str]] = {
    "PKO":   ["PKO"],
    "CDR":   ["CDPROJEKT", "CD PROJEKT"],
    "KGHM":  ["KGHM"],
    "PZU":   ["PZU"],
    "MBK":   ["MBANK"],
    "LPP":   ["LPP"],
    "ALE":   ["ALLEGRO"],
    "DNP":   ["DINO"],
    "BDX":   ["BUDIMEX"],
    "PKN":   ["ORLEN", "PKNO"],
    "OPL":   ["ORANGE"],
    "CPS":   ["POLSAT", "CYFROWY"],
    "JSW":   ["JSW"],
    "CCC":   ["CCC"],
    "TPE":   ["TAURON"],
    "PGE":   ["PGE"],
}


def analyze_insider_transactions(ticker: str) -> PatternResult | None:
    try:
        from datetime import timedelta

        from bs4 import BeautifulSoup

        names = _BANKIER_NAME_MAP.get(ticker.upper(), [ticker.upper()])
        cutoff = date.today() - timedelta(days=90)

        buys, sells, other = 0, 0, 0
        total_buy_value, total_sell_value = 0.0, 0.0
        found = 0

        for page in range(1, 6):
            url = f"https://www.bankier.pl/gielda/transakcje-insiderow?page={page}"
            req = urllib.request.Request(url, headers=_BR_HEADERS)
            with urllib.request.urlopen(req, timeout=8) as r:
                soup = BeautifulSoup(r.read(), "lxml")

            table = soup.find("table")
            if not table:
                break

            rows = table.find_all("tr")[1:]
            page_found = 0
            all_too_old = True  # czy wszystkie pasujące transakcje na tej stronie są sprzed cutoff

            for row in rows:
                cells = [td.get_text(strip=True) for td in row.find_all(["td", "th"])]
                if len(cells) < 6:
                    continue

                spolka = cells[0].upper().replace(" ", "").replace(".", "")
                match = any(n.replace(" ", "") in spolka or spolka.startswith(n.replace(" ", ""))
                            for n in names)
                if not match:
                    continue

                # Parsuj datę
                date_str = cells[6] if len(cells) > 6 else cells[-1]
                try:
                    tx_date = date.fromisoformat(date_str.strip()[:10])
                except ValueError:
                    continue
                if tx_date < cutoff:
                    continue

                all_too_old = False
                found += 1
                page_found += 1
                tx_type = cells[2].lower()
                val_raw = cells[5].replace("\xa0", "").replace(" ", "").replace("zł", "").replace(",", ".")
                try:
                    val = float(re.sub(r"[^\d.]", "", val_raw))
                except ValueError:
                    val = 0.0

                if "kupno" in tx_type or "nabycie" in tx_type:
                    buys += 1
                    total_buy_value += val
                elif "sprzedaż" in tx_type or "zbycie" in tx_type:
                    sells += 1
                    total_sell_value += val
                else:
                    other += 1

            # Jeśli na tej stronie nie było żadnej transakcji w oknie 90 dni — kończymy
            if all_too_old and page_found == 0:
                break

        total = buys + sells
        if total == 0:
            return None

        direction = "UP" if buys > sells else "DOWN" if sells > buys else "NEUTRAL"
        prob = buys / total if direction == "UP" else sells / total
        prob = min(max(prob, 0.5), 0.80)
        strength = "strong" if prob >= 0.75 and total >= 3 else "medium" if prob >= 0.6 else "weak"

        buy_str = f"{total_buy_value/1e6:.1f}M PLN" if total_buy_value >= 1e6 else f"{total_buy_value/1e3:.0f}k PLN"
        sell_str = f"{total_sell_value/1e6:.1f}M PLN" if total_sell_value >= 1e6 else f"{total_sell_value/1e3:.0f}k PLN"

        parts = []
        if buys:
            parts.append(f"Kupno: {buys}×({buy_str})")
        if sells:
            parts.append(f"Sprzedaż: {sells}×({sell_str})")

        return PatternResult(
            name="Transakcje insiderów",
            direction=direction, strength=strength, probability=prob,
            sample_size=total, avg_return=None, horizon_days=60,
            note=f"Ostatnie 90 dni: {', '.join(parts)}",
        )
    except Exception:
        return None


# ── Katalyzatory ─────────────────────────────────────────────────────────────

def get_catalysts(yahoo_ticker: str) -> list[Catalyst]:
    catalysts: list[Catalyst] = []
    today = date.today()
    try:
        cal = yf.Ticker(yahoo_ticker).calendar
        if not cal:
            return catalysts

        ex_div = cal.get("Ex-Dividend Date")
        if ex_div and hasattr(ex_div, "year"):
            days = (ex_div - today).days
            if -30 <= days <= 120:
                catalysts.append(Catalyst(
                    name="Ex-dywidenda", event_date=ex_div, days_away=days,
                    description="Dzień odcięcia dywidendy",
                ))

        earn_dates = cal.get("Earnings Date", [])
        earn_date = earn_dates[0] if isinstance(earn_dates, list) and earn_dates else (
            earn_dates if hasattr(earn_dates, "year") else None)
        if earn_date and hasattr(earn_date, "year"):
            days = (earn_date - today).days
            if -10 <= days <= 120:
                catalysts.append(Catalyst(
                    name="Raport wynikowy", event_date=earn_date, days_away=days,
                    description="Publikacja wyników kwartalnych",
                ))
    except Exception:
        pass

    return sorted(catalysts, key=lambda c: c.days_away)


# ── Główna funkcja ────────────────────────────────────────────────────────────

def run_all_patterns(
    yahoo_ticker: str, ticker: str, industry: str | None = None,
) -> tuple[list[PatternResult], list[Catalyst]]:
    df = _fetch_price_history(yahoo_ticker)
    if df.empty:
        return [], []

    gpw = is_gpw(ticker)
    bench_label = "WIG20" if gpw else "S&P500"
    benchmark = _fetch_benchmark(ticker)
    sector_ticker = _SECTOR_MAP.get(ticker.upper()) if gpw else None
    sector_df = _fetch_price_history(sector_ticker) if sector_ticker else None
    sector_name = sector_ticker.replace(".WA", "") if sector_ticker else "sektor"

    catalysts = get_catalysts(yahoo_ticker)
    if is_gaming_company(ticker, industry):
        catalysts.extend(gaming_event_catalysts())
        catalysts.sort(key=lambda c: c.days_away)

    try:
        raw_divs = yf.Ticker(yahoo_ticker).dividends
        div_dates = [d.date() if hasattr(d, "date") else d for d in raw_divs.index.tolist()]
    except Exception:
        div_dates = []

    try:
        earnings = yf.Ticker(yahoo_ticker).earnings_dates
        earnings = earnings.dropna(subset=["Reported EPS"]) if earnings is not None else pd.DataFrame()
    except Exception:
        earnings = pd.DataFrame()

    patterns: list[PatternResult] = []
    patterns.extend(analyze_dividend_pattern(df, div_dates))
    patterns.extend(analyze_earnings_pattern(df, earnings))

    vol = analyze_volume(df)
    if vol:
        patterns.append(vol)

    pos_52w = analyze_52w_position(df)
    if pos_52w:
        patterns.append(pos_52w)

    patterns.extend(analyze_momentum(df, benchmark, sector_df, sector_name, bench_label))

    seasonal = analyze_seasonality(df)
    if seasonal:
        patterns.append(seasonal)

    if gpw:
        rec = analyze_analyst_recommendations(ticker)
        if rec:
            patterns.append(rec)

        insiders = analyze_insider_transactions(ticker)
        if insiders:
            patterns.append(insiders)

    return patterns, catalysts

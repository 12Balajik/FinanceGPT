# app/routes/ticker_routes.py

from fastapi import APIRouter
from typing import List
import yfinance as yf

router = APIRouter()

POPULAR_TICKERS = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "TSLA",
    "NVDA", "META", "NFLX", "AMD", "JPM"
]


@router.get("/ticker-stats")
def get_ticker_stats():
    """
    Lightweight live stats for a fixed set of popular tickers.
    No LLM call — used for the scrolling ticker strip on the frontend.
    """
    results = []
    data = yf.Tickers(" ".join(POPULAR_TICKERS))

    for symbol in POPULAR_TICKERS:
        try:
            info = data.tickers[symbol].fast_info
            price = info.get("lastPrice")
            prev_close = info.get("previousClose")
            change_pct = None
            if price is not None and prev_close:
                change_pct = round(((price - prev_close) / prev_close) * 100, 2)

            results.append({
                "ticker": symbol,
                "price": round(price, 2) if price is not None else None,
                "change_pct": change_pct,
            })
        except Exception:
            results.append({
                "ticker": symbol,
                "price": None,
                "change_pct": None,
            })

    return {"stocks": results}
# app/routes/watchlist_routes.py

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
import yfinance as yf
from app.database import get_db, WatchlistItem

router = APIRouter()


class AddTickerRequest(BaseModel):
    ticker: str
    notes: Optional[str] = None


@router.get("/watchlist")
def get_watchlist(db: Session = Depends(get_db)):
    """Return all watchlist items with live prices."""
    items = db.query(WatchlistItem).order_by(WatchlistItem.added_at).all()
    if not items:
        return {"watchlist": []}

    tickers = [i.ticker for i in items]
    live_data = {}

    try:
        data = yf.download(
            tickers=tickers,
            period="2d",
            interval="1d",
            group_by="ticker",
            progress=False,
            threads=True,
        )
        for ticker in tickers:
            try:
                if len(tickers) == 1:
                    closes = data["Close"].dropna()
                else:
                    closes = data[ticker]["Close"].dropna()
                if len(closes) >= 2:
                    price = float(closes.iloc[-1])
                    prev = float(closes.iloc[-2])
                    change_pct = round((price - prev) / prev * 100, 2)
                elif len(closes) == 1:
                    price = float(closes.iloc[-1])
                    prev = price
                    change_pct = 0.0
                else:
                    raise ValueError("no data")
                live_data[ticker] = {"price": round(price, 2), "change_pct": change_pct, "prev_close": round(prev, 2)}
            except Exception:
                live_data[ticker] = {"price": None, "change_pct": None, "prev_close": None}
    except Exception:
        for ticker in tickers:
            live_data[ticker] = {"price": None, "change_pct": None, "prev_close": None}

    result = []
    for item in items:
        ld = live_data.get(item.ticker, {})
        result.append({
            "ticker": item.ticker,
            "company_name": item.company_name,
            "notes": item.notes,
            "added_at": item.added_at.isoformat() if item.added_at else None,
            "price": ld.get("price"),
            "change_pct": ld.get("change_pct"),
            "prev_close": ld.get("prev_close"),
        })

    return {"watchlist": result}


@router.post("/watchlist")
def add_to_watchlist(body: AddTickerRequest, db: Session = Depends(get_db)):
    """Add a ticker to the watchlist."""
    ticker = body.ticker.strip().upper()
    if not ticker:
        raise HTTPException(status_code=400, detail="Ticker cannot be empty.")

    existing = db.query(WatchlistItem).filter(WatchlistItem.ticker == ticker).first()
    if existing:
        raise HTTPException(status_code=409, detail=f"{ticker} is already in your watchlist.")

    # Verify ticker exists
    try:
        info = yf.Ticker(ticker).fast_info
        price = info.get("lastPrice")
        company = None
        if price is None:
            raise ValueError("invalid")
        try:
            company = yf.Ticker(ticker).info.get("longName") or ticker
        except Exception:
            company = ticker
    except Exception:
        raise HTTPException(status_code=404, detail=f"Could not find ticker '{ticker}'. Check the symbol.")

    item = WatchlistItem(ticker=ticker, company_name=company, notes=body.notes)
    db.add(item)
    db.commit()
    return {"message": f"{ticker} added to watchlist.", "ticker": ticker, "company_name": company}


@router.delete("/watchlist/{ticker}")
def remove_from_watchlist(ticker: str, db: Session = Depends(get_db)):
    """Remove a ticker from the watchlist."""
    ticker = ticker.upper().strip()
    item = db.query(WatchlistItem).filter(WatchlistItem.ticker == ticker).first()
    if not item:
        raise HTTPException(status_code=404, detail=f"{ticker} not found in watchlist.")
    db.delete(item)
    db.commit()
    return {"message": f"{ticker} removed from watchlist."}
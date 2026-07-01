 # app/routes/watchlist_routes.py

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
import yfinance as yf
from app.database import get_db, WatchlistItem, User
from app.services.auth_service import get_current_user

router = APIRouter()


class AddTickerRequest(BaseModel):
    ticker: str
    notes: Optional[str] = None


@router.get("/watchlist")
def get_watchlist(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    items = db.query(WatchlistItem).filter(
        WatchlistItem.user_id == current_user.id
    ).order_by(WatchlistItem.added_at).all()

    if not items:
        return {"watchlist": []}

    tickers = [i.ticker for i in items]
    live_data = {}

    try:
        data = yf.download(
            tickers=tickers, period="2d", interval="1d",
            group_by="ticker", progress=False, threads=True,
        )
        for ticker in tickers:
            try:
                closes = data["Close"].dropna() if len(tickers) == 1 else data[ticker]["Close"].dropna()
                if len(closes) >= 2:
                    price = float(closes.iloc[-1])
                    prev = float(closes.iloc[-2])
                    change_pct = round((price - prev) / prev * 100, 2)
                elif len(closes) == 1:
                    price = float(closes.iloc[-1])
                    prev = price
                    change_pct = 0.0
                else:
                    raise ValueError()
                live_data[ticker] = {"price": round(price, 2), "change_pct": change_pct}
            except Exception:
                live_data[ticker] = {"price": None, "change_pct": None}
    except Exception:
        for ticker in tickers:
            live_data[ticker] = {"price": None, "change_pct": None}

    return {
        "watchlist": [{
            "id": item.id,
            "ticker": item.ticker,
            "company_name": item.company_name,
            "notes": item.notes,
            "added_at": item.added_at.isoformat() if item.added_at else None,
            "price": live_data.get(item.ticker, {}).get("price"),
            "change_pct": live_data.get(item.ticker, {}).get("change_pct"),
        } for item in items]
    }


@router.post("/watchlist")
def add_to_watchlist(
    body: AddTickerRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    ticker = body.ticker.strip().upper()

    existing = db.query(WatchlistItem).filter(
        WatchlistItem.user_id == current_user.id,
        WatchlistItem.ticker == ticker
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail=f"{ticker} is already in your watchlist.")

    company_name = ticker
    try:
        info = yf.Ticker(ticker).fast_info
        if info.get("lastPrice") is None:
            raise ValueError()
        try:
            company_name = yf.Ticker(ticker).info.get("longName") or ticker
        except Exception:
            pass
    except Exception:
        raise HTTPException(status_code=404, detail=f"Could not find ticker '{ticker}'.")

    item = WatchlistItem(
        user_id=current_user.id,
        ticker=ticker,
        company_name=company_name,
        notes=body.notes
    )
    db.add(item)
    db.commit()
    return {"message": f"{ticker} added to watchlist.", "ticker": ticker}


@router.delete("/watchlist/{item_id}")
def remove_from_watchlist(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    item = db.query(WatchlistItem).filter(
        WatchlistItem.id == item_id,
        WatchlistItem.user_id == current_user.id
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found.")
    db.delete(item)
    db.commit()
    return {"message": f"{item.ticker} removed from watchlist."}
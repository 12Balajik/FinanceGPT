# app/routes/portfolio_routes.py

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
import yfinance as yf
from app.database import get_db, PortfolioPosition

router = APIRouter()


class AddPositionRequest(BaseModel):
    ticker: str
    quantity: float
    buy_price: float


@router.get("/portfolio")
def get_portfolio(db: Session = Depends(get_db)):
    positions = db.query(PortfolioPosition).order_by(PortfolioPosition.added_at).all()
    if not positions:
        return {
            "positions": [],
            "summary": {
                "total_invested": 0,
                "total_value": 0,
                "total_pnl": 0,
                "total_pnl_pct": 0
            }
        }

    tickers = list(set([p.ticker for p in positions]))
    live_prices = {}

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
                if len(closes) >= 1:
                    live_prices[ticker] = round(float(closes.iloc[-1]), 2)
                else:
                    live_prices[ticker] = None
            except Exception:
                live_prices[ticker] = None
    except Exception:
        for ticker in tickers:
            live_prices[ticker] = None

    result = []
    total_invested = 0
    total_value = 0

    for pos in positions:
        current_price = live_prices.get(pos.ticker)
        invested = round(pos.quantity * pos.buy_price, 2)
        current_value = round(pos.quantity * current_price, 2) if current_price else None
        pnl = round(current_value - invested, 2) if current_value is not None else None
        pnl_pct = round((pnl / invested) * 100, 2) if pnl is not None and invested > 0 else None

        total_invested += invested
        if current_value is not None:
            total_value += current_value

        result.append({
            "id": pos.id,
            "ticker": pos.ticker,
            "company_name": pos.company_name,
            "quantity": pos.quantity,
            "buy_price": pos.buy_price,
            "current_price": current_price,
            "invested": invested,
            "current_value": current_value,
            "pnl": pnl,
            "pnl_pct": pnl_pct,
            "added_at": pos.added_at.isoformat() if pos.added_at else None,
        })

    total_pnl = round(total_value - total_invested, 2)
    total_pnl_pct = round((total_pnl / total_invested) * 100, 2) if total_invested > 0 else 0

    return {
        "positions": result,
        "summary": {
            "total_invested": round(total_invested, 2),
            "total_value": round(total_value, 2),
            "total_pnl": total_pnl,
            "total_pnl_pct": total_pnl_pct,
        }
    }


@router.post("/portfolio")
def add_position(body: AddPositionRequest, db: Session = Depends(get_db)):
    ticker = body.ticker.strip().upper()

    if body.quantity <= 0:
        raise HTTPException(status_code=400, detail="Quantity must be greater than 0.")
    if body.buy_price <= 0:
        raise HTTPException(status_code=400, detail="Buy price must be greater than 0.")

    company_name = ticker
    try:
        info = yf.Ticker(ticker).fast_info
        if info.get("lastPrice") is None:
            raise ValueError("invalid")
        try:
            company_name = yf.Ticker(ticker).info.get("longName") or ticker
        except Exception:
            company_name = ticker
    except Exception:
        raise HTTPException(status_code=404, detail=f"Could not find ticker '{ticker}'.")

    position = PortfolioPosition(
        ticker=ticker,
        company_name=company_name,
        quantity=body.quantity,
        buy_price=body.buy_price,
    )
    db.add(position)
    db.commit()
    db.refresh(position)

    return {
        "message": f"Added {body.quantity} shares of {ticker} at ${body.buy_price}.",
        "id": position.id,
        "ticker": ticker,
        "company_name": company_name,
    }


@router.delete("/portfolio/{position_id}")
def remove_position(position_id: int, db: Session = Depends(get_db)):
    position = db.query(PortfolioPosition).filter(PortfolioPosition.id == position_id).first()
    if not position:
        raise HTTPException(status_code=404, detail="Position not found.")
    db.delete(position)
    db.commit()
    return {"message": "Position removed successfully."}
# app/routes/alert_routes.py

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timezone
import yfinance as yf
from app.database import get_db, PriceAlert

router = APIRouter()


class AddAlertRequest(BaseModel):
    ticker: str
    target_price: float
    direction: str  # "above" or "below"


@router.get("/alerts")
def get_alerts(db: Session = Depends(get_db)):
    alerts = db.query(PriceAlert).order_by(PriceAlert.created_at.desc()).all()
    return {
        "alerts": [
            {
                "id": a.id,
                "ticker": a.ticker,
                "company_name": a.company_name,
                "target_price": a.target_price,
                "direction": a.direction,
                "fired": a.fired,
                "fired_at": a.fired_at.isoformat() if a.fired_at else None,
                "created_at": a.created_at.isoformat() if a.created_at else None,
            }
            for a in alerts
        ]
    }


@router.post("/alerts")
def add_alert(body: AddAlertRequest, db: Session = Depends(get_db)):
    ticker = body.ticker.strip().upper()
    direction = body.direction.lower().strip()

    if direction not in ("above", "below"):
        raise HTTPException(status_code=400, detail="Direction must be 'above' or 'below'.")
    if body.target_price <= 0:
        raise HTTPException(status_code=400, detail="Target price must be greater than 0.")

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

    alert = PriceAlert(
        ticker=ticker,
        company_name=company_name,
        target_price=body.target_price,
        direction=direction,
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)

    return {
        "message": f"Alert set: {ticker} {direction} ${body.target_price}",
        "id": alert.id,
        "ticker": ticker,
        "company_name": company_name,
    }


@router.delete("/alerts/{alert_id}")
def remove_alert(alert_id: int, db: Session = Depends(get_db)):
    alert = db.query(PriceAlert).filter(PriceAlert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found.")
    db.delete(alert)
    db.commit()
    return {"message": "Alert removed."}


@router.post("/alerts/check")
def check_alerts(db: Session = Depends(get_db)):
    """Check all active alerts against live prices and fire if triggered."""
    active = db.query(PriceAlert).filter(PriceAlert.fired == False).all()
    if not active:
        return {"fired": [], "checked": 0}

    tickers = list(set([a.ticker for a in active]))
    live_prices = {}

    try:
        data = yf.download(
            tickers=tickers,
            period="1d",
            interval="1m",
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
            except Exception:
                pass
    except Exception:
        pass

    fired = []
    for alert in active:
        price = live_prices.get(alert.ticker)
        if price is None:
            continue
        triggered = (
            alert.direction == "above" and price >= alert.target_price
        ) or (
            alert.direction == "below" and price <= alert.target_price
        )
        if triggered:
            alert.fired = True
            alert.fired_at = datetime.now(timezone.utc)
            db.commit()
            fired.append({
                "id": alert.id,
                "ticker": alert.ticker,
                "target_price": alert.target_price,
                "direction": alert.direction,
                "current_price": price,
            })

    return {"fired": fired, "checked": len(active)}
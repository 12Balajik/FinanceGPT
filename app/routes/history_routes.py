# app/routes/history_routes.py

from fastapi import APIRouter, HTTPException, Query
import yfinance as yf

router = APIRouter()

VALID_PERIODS = {
    "1W": "5d",
    "1M": "1mo",
    "3M": "3mo",
    "6M": "6mo",
    "1Y": "1y",
}


@router.get("/history/{ticker}")
def get_history(
    ticker: str,
    period: str = Query(default="1M"),
):
    ticker = ticker.upper().strip()
    yf_period = VALID_PERIODS.get(period.upper())

    if not yf_period:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid period. Choose from: {', '.join(VALID_PERIODS.keys())}"
        )

    try:
        hist = yf.Ticker(ticker).history(period=yf_period)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    if hist.empty:
        raise HTTPException(status_code=404, detail=f"No history for '{ticker}'.")

    return {
        "ticker": ticker,
        "period": period.upper(),
        "labels": [str(d.date()) for d in hist.index],
        "prices": [round(float(p), 2) for p in hist["Close"]],
        "volumes": [int(v) for v in hist["Volume"]],
    }
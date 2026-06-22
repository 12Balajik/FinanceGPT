# app/routes/compare_routes.py

import time
from fastapi import APIRouter, HTTPException, Query
from typing import List
from app.services.stock_service import get_stock_data
from app.services.llm_service import get_compare_analysis
from app.models.schemas import StockData

router = APIRouter()


@router.get("/compare")
def compare_stocks(tickers: str = Query(..., description="Comma-separated tickers e.g. AAPL,MSFT,TSLA")):
    """
    Fetch real-time data for multiple tickers and return an AI comparison.
    """
    symbols = [t.strip().upper() for t in tickers.split(",") if t.strip()]

    if len(symbols) < 2:
        raise HTTPException(status_code=400, detail="Provide at least 2 tickers to compare.")
    if len(symbols) > 5:
        raise HTTPException(status_code=400, detail="Maximum 5 tickers per comparison.")

    stocks = []
    failed = []

    for symbol in symbols:
        try:
            stock = get_stock_data(symbol)
            stocks.append(stock)
        except ValueError:
            failed.append(symbol)

    if len(stocks) < 2:
        raise HTTPException(status_code=404, detail=f"Could not fetch data for enough tickers. Failed: {failed}")

    t0 = time.time()
    analysis = get_compare_analysis(stocks)
    print(f"[TIMING] Compare LLM analysis: {time.time() - t0:.2f}s")

    return {
        "tickers": [s.ticker for s in stocks],
        "stocks": [s.model_dump() for s in stocks],
        "failed": failed,
        "ai_analysis": analysis,
    }
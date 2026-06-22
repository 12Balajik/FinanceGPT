import time
from fastapi import APIRouter, HTTPException
from app.services.stock_service import get_stock_data
from app.services.llm_service import get_ai_analysis
from app.models.schemas import AnalysisResponse

router = APIRouter()


@router.get("/analyze/{ticker}", response_model=AnalysisResponse)
def analyze_stock(ticker: str):
    t0 = time.time()
    try:
        stock = get_stock_data(ticker)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    t1 = time.time()
    print(f"[TIMING] yfinance fetch: {t1 - t0:.2f}s")

    try:
        analysis = get_ai_analysis(stock)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    t2 = time.time()
    print(f"[TIMING] LLM analysis: {t2 - t1:.2f}s")
    print(f"[TIMING] TOTAL: {t2 - t0:.2f}s")

    return AnalysisResponse(
        ticker=stock.ticker,
        stock_data=stock,
        ai_analysis=analysis,
    )
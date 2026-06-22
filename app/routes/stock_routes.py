 # app/routes/stock_routes.py

import time
from fastapi import APIRouter, HTTPException
from app.services.stock_service import get_stock_data
from app.services.llm_service import get_ai_analysis

router = APIRouter()


def parse_analysis(raw: str) -> dict:
    result = {
        "signal": "HOLD",
        "confidence": "LOW",
        "summary": raw,
        "reasoning": "",
        "disclaimer": "This is AI-generated analysis for educational purposes only, not financial advice.",
    }

    current_key = None
    for line in raw.strip().splitlines():
        line = line.strip()
        if line.startswith("SIGNAL:"):
            val = line.replace("SIGNAL:", "").strip().upper()
            if val in ("BUY", "HOLD", "SELL"):
                result["signal"] = val
        elif line.startswith("CONFIDENCE:"):
            val = line.replace("CONFIDENCE:", "").strip().upper()
            if val in ("HIGH", "MEDIUM", "LOW"):
                result["confidence"] = val
        elif line.startswith("SUMMARY:"):
            result["summary"] = line.replace("SUMMARY:", "").strip()
            current_key = "summary"
        elif line.startswith("REASONING:"):
            result["reasoning"] = line.replace("REASONING:", "").strip()
            current_key = "reasoning"
        elif line.startswith("DISCLAIMER:"):
            result["disclaimer"] = line.replace("DISCLAIMER:", "").strip()
            current_key = None
        elif line and current_key in ("summary", "reasoning"):
            result[current_key] += " " + line

    return result


@router.get("/analyze/{ticker}")
def analyze_stock(ticker: str):
    t0 = time.time()
    try:
        stock = get_stock_data(ticker)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    t1 = time.time()
    print(f"[TIMING] yfinance fetch: {t1 - t0:.2f}s")

    try:
        raw_analysis = get_ai_analysis(stock)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    t2 = time.time()
    print(f"[TIMING] LLM analysis: {t2 - t1:.2f}s")
    print(f"[TIMING] TOTAL: {t2 - t0:.2f}s")

    parsed = parse_analysis(raw_analysis)

    return {
        "ticker": stock.ticker,
        "stock_data": stock.model_dump(),
        "signal": parsed["signal"],
        "confidence": parsed["confidence"],
        "ai_analysis": parsed["summary"],
        "reasoning": parsed["reasoning"],
        "disclaimer": parsed["disclaimer"],
    }
 # app/services/llm_service.py

import time
import requests
from app.config import settings
from app.models.schemas import StockData


def build_analysis_prompt(stock: StockData) -> str:
    return f"""You are an AI financial analyst. Analyze the following stock data and respond in exactly this format — no extra text, no markdown:

SIGNAL: [BUY or HOLD or SELL]
CONFIDENCE: [HIGH or MEDIUM or LOW]
SUMMARY: [2-3 sentence analysis of the stock's current position, valuation, and price action]
REASONING: [2-3 sentences explaining why you gave this signal, based purely on the data provided]
DISCLAIMER: This is AI-generated analysis for educational purposes only, not financial advice.

Stock Data:
Ticker: {stock.ticker}
Company: {stock.company_name}
Current Price: ${stock.current_price}
Previous Close: ${stock.previous_close}
Day Range: ${stock.day_low} - ${stock.day_high}
52-Week Range: ${stock.fifty_two_week_low} - ${stock.fifty_two_week_high}
Volume: {stock.volume}
Market Cap: {stock.market_cap}
P/E Ratio: {stock.pe_ratio}

Respond strictly in the format above:"""


def get_ai_analysis(stock: StockData) -> str:
    prompt = build_analysis_prompt(stock)

    url = f"{settings.OLLAMA_BASE_URL}/api/generate"
    payload = {
        "model": settings.OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
    }

    print("[TIMING] Sending request to Ollama...")
    start = time.time()

    try:
        response = requests.post(url, json=payload, timeout=settings.OLLAMA_TIMEOUT)
        response.raise_for_status()
    except requests.exceptions.ConnectionError:
        raise RuntimeError("Could not connect to Ollama. Make sure the Ollama app is running.")
    except requests.exceptions.Timeout:
        raise RuntimeError("Ollama took too long to respond (timeout).")
    except requests.exceptions.HTTPError as e:
        raise RuntimeError(f"Ollama returned an error: {str(e)}")

    elapsed = time.time() - start
    print(f"[TIMING] Ollama responded in {elapsed:.2f}s")

    data = response.json()

    if "total_duration" in data:
        print(f"[TIMING] Ollama internal total_duration: {data['total_duration'] / 1e9:.2f}s")
    if "eval_count" in data and "eval_duration" in data:
        tokens_per_sec = data["eval_count"] / (data["eval_duration"] / 1e9)
        print(f"[TIMING] Generation speed: {tokens_per_sec:.1f} tokens/sec")

    return data.get("response", "").strip()
def build_compare_prompt(stocks: list) -> str:
    lines = []
    for s in stocks:
        lines.append(f"""
{s.ticker} — {s.company_name}
  Price: ${s.current_price} | Prev Close: ${s.previous_close}
  Day Range: ${s.day_low} – ${s.day_high}
  52w Range: ${s.fifty_two_week_low} – ${s.fifty_two_week_high}
  Market Cap: {s.market_cap} | P/E: {s.pe_ratio} | Volume: {s.volume}""")

    stock_block = "\n".join(lines)

    return f"""You are a financial analyst. Compare the following stocks objectively and concisely (4-6 sentences). Highlight key differences in valuation, price momentum, and market cap. Do not give buy/sell advice.

{stock_block}

Comparison:"""


def get_compare_analysis(stocks: list) -> str:
    prompt = build_compare_prompt(stocks)
    url = f"{settings.OLLAMA_BASE_URL}/api/generate"
    payload = {
        "model": settings.OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
    }

    try:
        response = requests.post(url, json=payload, timeout=settings.OLLAMA_TIMEOUT)
        response.raise_for_status()
    except requests.exceptions.ConnectionError:
        raise RuntimeError("Could not connect to Ollama.")
    except requests.exceptions.Timeout:
        raise RuntimeError("Ollama timed out.")
    except requests.exceptions.HTTPError as e:
        raise RuntimeError(f"Ollama error: {str(e)}")

    return response.json().get("response", "").strip()
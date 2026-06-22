 # app/services/llm_service.py

import time
import requests
from app.config import settings
from app.models.schemas import StockData


def build_analysis_prompt(stock: StockData) -> str:
    return f"""You are a financial analyst assistant. Analyze the following stock data and provide a concise, professional summary (3-5 sentences). Mention valuation, recent price action, and any notable observations. Do not give direct buy/sell advice — only factual analysis.

Ticker: {stock.ticker}
Company: {stock.company_name}
Current Price: {stock.current_price}
Previous Close: {stock.previous_close}
Day Range: {stock.day_low} - {stock.day_high}
52-Week Range: {stock.fifty_two_week_low} - {stock.fifty_two_week_high}
Volume: {stock.volume}
Market Cap: {stock.market_cap}
P/E Ratio: {stock.pe_ratio}

Provide your analysis:"""


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
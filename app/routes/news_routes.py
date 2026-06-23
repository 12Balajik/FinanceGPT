# app/routes/news_routes.py

from fastapi import APIRouter, HTTPException
import yfinance as yf
import requests as http_requests
from app.config import settings

router = APIRouter()


def summarize_news(ticker: str, headlines: list) -> str:
    headline_block = "\n".join(
        [f"- {h['title']} ({h['publisher']})" for h in headlines[:8]]
    )

    prompt = f"""You are a financial news analyst. Based on the following recent headlines about {ticker}, provide:

SENTIMENT: [POSITIVE or NEGATIVE or NEUTRAL or MIXED]
SUMMARY: [2-3 sentences summarizing the key themes and overall sentiment from these headlines]
KEY_THEMES: [comma-separated list of 3-5 key themes or topics from the news]

Headlines:
{headline_block}

Respond strictly in the format above:"""

    payload = {
        "model": settings.OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
    }

    try:
        response = http_requests.post(
            f"{settings.OLLAMA_BASE_URL}/api/generate",
            json=payload,
            timeout=settings.OLLAMA_TIMEOUT,
        )
        response.raise_for_status()
        return response.json().get("response", "").strip()
    except Exception as e:
        return f"Could not generate news summary: {str(e)}"


def parse_news_analysis(raw: str) -> dict:
    result = {
        "sentiment": "NEUTRAL",
        "summary": raw,
        "key_themes": [],
    }
    current_key = None
    for line in raw.strip().splitlines():
        line = line.strip()
        if line.startswith("SENTIMENT:"):
            val = line.replace("SENTIMENT:", "").strip().upper()
            if val in ("POSITIVE", "NEGATIVE", "NEUTRAL", "MIXED"):
                result["sentiment"] = val
        elif line.startswith("SUMMARY:"):
            result["summary"] = line.replace("SUMMARY:", "").strip()
            current_key = "summary"
        elif line.startswith("KEY_THEMES:"):
            themes = line.replace("KEY_THEMES:", "").strip()
            result["key_themes"] = [t.strip() for t in themes.split(",") if t.strip()]
            current_key = None
        elif line and current_key == "summary":
            result["summary"] += " " + line
    return result


@router.get("/news/{ticker}")
def get_news(ticker: str):
    ticker = ticker.upper().strip()

    try:
        stock = yf.Ticker(ticker)
        news = stock.news
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch news: {str(e)}")

    if not news:
        raise HTTPException(status_code=404, detail=f"No news found for '{ticker}'.")

    # Extract clean headline data
    headlines = []
    for item in news[:10]:
        content = item.get("content", {})
        title = content.get("title") or item.get("title", "")
        publisher = content.get("provider", {}).get("displayName", "") or item.get("publisher", "")
        link = content.get("canonicalUrl", {}).get("url", "") or item.get("link", "")
        pub_date = content.get("pubDate", "") or ""

        if title:
            headlines.append({
                "title": title,
                "publisher": publisher,
                "link": link,
                "published": pub_date[:10] if pub_date else "",
            })

    if not headlines:
        raise HTTPException(status_code=404, detail=f"No readable headlines for '{ticker}'.")

    raw_analysis = summarize_news(ticker, headlines)
    parsed = parse_news_analysis(raw_analysis)

    return {
        "ticker": ticker,
        "headline_count": len(headlines),
        "headlines": headlines,
        "sentiment": parsed["sentiment"],
        "summary": parsed["summary"],
        "key_themes": parsed["key_themes"],
    }
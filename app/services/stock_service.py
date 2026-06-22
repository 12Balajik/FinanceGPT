# app/services/stock_service.py

import yfinance as yf
from app.models.schemas import StockData


def get_stock_data(ticker: str) -> StockData:
    """
    Fetch current stock data for a given ticker symbol using yfinance.
    Raises ValueError if the ticker is invalid or no data is found.
    """
    ticker = ticker.upper().strip()
    stock = yf.Ticker(ticker)

    try:
        info = stock.info
    except Exception as e:
        raise ValueError(f"Failed to fetch data for '{ticker}': {str(e)}")

    # yfinance returns a near-empty dict for invalid tickers
    if not info or info.get("regularMarketPrice") is None and info.get("currentPrice") is None:
        raise ValueError(f"No data found for ticker '{ticker}'. It may be invalid or delisted.")

    current_price = info.get("currentPrice") or info.get("regularMarketPrice")

    return StockData(
        ticker=ticker,
        company_name=info.get("longName") or info.get("shortName"),
        current_price=current_price,
        previous_close=info.get("previousClose"),
        open_price=info.get("open"),
        day_high=info.get("dayHigh"),
        day_low=info.get("dayLow"),
        volume=info.get("volume"),
        market_cap=info.get("marketCap"),
        pe_ratio=info.get("trailingPE"),
        fifty_two_week_high=info.get("fiftyTwoWeekHigh"),
        fifty_two_week_low=info.get("fiftyTwoWeekLow"),
    )
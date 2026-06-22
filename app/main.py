 # app/main.py

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.routes.stock_routes import router as stock_router
from app.routes.ticker_routes import router as ticker_router
from app.routes.compare_routes import router as compare_router
from app.routes.history_routes import router as history_router
from app.routes.qa_routes import router as qa_router

app = FastAPI(
    title="FinanceGPT",
    description="AI-powered financial assistant using local LLM (Ollama + Llama 3.1) and Yahoo Finance data.",
    version="0.4.0",
)

app.include_router(stock_router)
app.include_router(ticker_router)
app.include_router(compare_router)
app.include_router(history_router)
app.include_router(qa_router)

app.mount("/static", StaticFiles(directory="frontend"), name="static")


@app.get("/")
def root():
    return FileResponse("frontend/index.html")


@app.get("/api")
def api_status():
    return {"status": "FinanceGPT API is running", "docs": "/docs"}
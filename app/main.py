 # app/main.py

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from app.database import init_db
from app.routes.stock_routes import router as stock_router
from app.routes.ticker_routes import router as ticker_router
from app.routes.compare_routes import router as compare_router
from app.routes.history_routes import router as history_router
from app.routes.qa_routes import router as qa_router
from app.routes.news_routes import router as news_router
from app.routes.watchlist_routes import router as watchlist_router
from app.routes.portfolio_routes import router as portfolio_router
from app.routes.alert_routes import router as alert_router
from app.routes.auth_routes import router as auth_router

app = FastAPI(
    title="FinanceGPT",
    description="AI-powered financial assistant using local LLM and Yahoo Finance.",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup():
    init_db()

app.include_router(auth_router)
app.include_router(stock_router)
app.include_router(ticker_router)
app.include_router(compare_router)
app.include_router(history_router)
app.include_router(qa_router)
app.include_router(news_router)
app.include_router(watchlist_router)
app.include_router(portfolio_router)
app.include_router(alert_router)

app.mount("/static", StaticFiles(directory="frontend"), name="static")

@app.get("/")
def root():
    return FileResponse("frontend/index.html")

@app.get("/api")
def api_status():
    return {"status": "FinanceGPT API is running", "version": "2.0.0"}
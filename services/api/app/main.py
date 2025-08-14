from fastapi import FastAPI, Depends, HTTPException, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from .routes import market, analysis, portfolio, lookup, metrics
from core.clients.dart import DARTClient
from core.services.market_data import dart_financials
import os
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())  # 루트 .env까지 탐색해서 로드

health = APIRouter()

app = FastAPI(title="Financial API")
app.include_router(market.router, prefix="/market", tags=["market"])
app.include_router(analysis.router, prefix="/analysis", tags=["analysis"])
app.include_router(portfolio.router, prefix="/portfolio", tags=["portfolio"])
app.include_router(lookup.router, prefix="/lookup", tags=["lookup"])
app.include_router(metrics.router, prefix="/metrics", tags=["metrics"])

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

market.setup_shutdown(app)

@app.get("/health")
async def _health():
    from datetime import datetime
    return {"ok": True, "ts": datetime.utcnow().isoformat()}

async def get_dart() -> DARTClient:
    return DARTClient(api_key=os.environ["API_KEY"])

# ✅ alias: allow /financials/{corp_or_stock}
@app.get("/financials/{code}")
async def financials_alias(code: str, year: int, dart: DARTClient = Depends(get_dart)):
    # If it's a 6-digit stock code, you must map to corp_code (see Option C)
    if len(code) == 8 and code.isdigit():
        corp_code = code
    else:
        # temporary: reject non-corp codes clearly
        raise HTTPException(400, detail="Use corp_code (e.g., 00126380) or enable Option C mapping")
    fs = await dart_financials(dart, corp_code, year)
    if not fs:
        raise HTTPException(404, detail="Financials not found")
    return fs
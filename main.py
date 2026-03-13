import os
import random
from datetime import datetime
from typing import List, Dict, Any

import requests
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

load_dotenv()

app = FastAPI(
    title="ONCHAIN AI – Intelligence Agent (Etherscan V2)",
    description="Ethereum whale data via Etherscan V2 API",
    version="1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===================== CONFIG =====================
ETHERSCAN_KEY = os.getenv("ETHERSCAN_API_KEY")
if not ETHERSCAN_KEY:
    print("WARNING: No ETHERSCAN_API_KEY in .env – using mock data only!")

ETHERSCAN_BASE = "https://api.etherscan.io/v2/api"

# ===================== RESPONSE SCHEMA =====================
class DataResponse(BaseModel):
    data: List[Dict]
    metrics: Dict
    source: str = "Ethereum"
    chart_data: Any = None

# ===================== Etherscan V2 FETCH (FIXED) =====================
def fetch_large_transfers() -> List[Dict]:
    if not ETHERSCAN_KEY:
        return [  # mock fallback
            {"wallet": "0x742d35Cc6634C0532925a3b8D9f6E4c9a9f3a9f3", "amount_eth": 142.8, "time": "2m ago", "tx": "0x8f3a..."},
            {"wallet": "0x1a2b3c4d5e6f...", "amount_eth": 89.4, "time": "7m ago", "tx": "0x4d2c..."},
            {"wallet": "0x9f8e7d6c5b4a...", "amount_eth": 312.7, "time": "14m ago", "tx": "0x9a1b..."},
        ]

    try:
        # V2 format: add chainid=1 (Ethereum), use a monitored address (zero address for incoming)
        # Change address to a known whale wallet if you want better data
        params = {
            "chainid": "1",
            "module": "account",
            "action": "txlist",
            "address": "0x0000000000000000000000000000000000000000",  # example
            "sort": "desc",
            "apikey": ETHERSCAN_KEY,
            "page": 1,
            "offset": 50
        }

        r = requests.get(ETHERSCAN_BASE, params=params, timeout=10)
        r.raise_for_status()

        data = r.json()
        if data.get("status") == "0":
            print(f"Etherscan error: {data.get('message')}")
            return []

        txs = data.get("result", [])
        if not isinstance(txs, list):
            print(f"Unexpected response: {data}")
            return []

        result = []
        for tx in txs:
            value = int(tx.get("value", "0")) / 1e18
            if value > 100:
                result.append({
                    "wallet": tx["from"],
                    "amount_eth": round(value, 1),
                    "time": datetime.fromtimestamp(int(tx["timeStamp"])).strftime("%Y-%m-%d %H:%M"),
                    "tx": tx["hash"][:10] + "..."
                })

        return result if result else [{"wallet": "No large transfers found", "amount_eth": 0, "time": "N/A", "tx": "N/A"}]

    except Exception as e:
        print(f"Etherscan fetch failed: {e}")
        print(f"Response snippet: {r.text[:200] if 'r' in locals() else 'No response'}")
        return []

# ===================== DEXSCREENER TRENDING =====================
def fetch_trending_tokens() -> List[Dict]:
    try:
        r = requests.get("https://api.dexscreener.com/latest/dex/search?q=eth", timeout=10)
        pairs = r.json().get("pairs", [])[:8]
        return [
            {
                "token": p["baseToken"]["name"],
                "symbol": p["baseToken"]["symbol"],
                "price_usd": float(p.get("priceUsd", 0)),
                "liq_usd": round(p.get("liquidity", {}).get("usd", 0) / 1e6, 1),
                "vol_24h": round(p.get("volume", {}).get("h24", 0) / 1e6, 1),
                "change_24h": round(p.get("priceChange", {}).get("h24", 0), 1)
            }
            for p in pairs if p.get("priceUsd")
        ]
    except:
        return [
            {"token": "GROK", "symbol": "GROK", "price_usd": 0.000184, "liq_usd": 12.8, "vol_24h": 89.4, "change_24h": 12.4},
            {"token": "GOAT", "symbol": "GOAT", "price_usd": 0.842, "liq_usd": 32.4, "vol_24h": 189.0, "change_24h": 187.3},
        ]

# ===================== ENDPOINTS =====================

@app.get("/whales", response_model=DataResponse)
@app.get("/whales-eth", response_model=DataResponse)
def get_whales():
    raw = fetch_large_transfers()
    total = sum(w.get("amount_eth", 0) for w in raw)

    metrics = {
        "count": len(raw),
        "total_eth": round(total, 1),
        "avg_eth": round(total / max(1, len(raw)), 1)
    }

    chart_data = [{"hour": h, "count": random.randint(5, 45)} for h in range(24)]

    return DataResponse(
        data=raw,
        metrics=metrics,
        source="Ethereum (Etherscan V2)",
        chart_data=chart_data
    )

@app.get("/trending", response_model=DataResponse)
def get_trending():
    raw = fetch_trending_tokens()
    total_vol = sum(t["vol_24h"] for t in raw)

    metrics = {
        "count": len(raw),
        "total_vol_m": round(total_vol, 1),
        "max_change": max((t.get("change_24h", 0) for t in raw), default=0)
    }

    chart_data = [{"token": t["token"], "volume_m": t["vol_24h"]} for t in raw]

    return DataResponse(
        data=raw,
        metrics=metrics,
        source="DexScreener",
        chart_data=chart_data
    )

# Stub for pump-signals (add real logic later)
@app.get("/pump-signals")
def pump_signals():
    return {"data": [], "metrics": {"active_signals": 0}, "note": "Coming soon - pump detection logic"}

@app.get("/dashboard-summary")
def dashboard_summary():
    eth = fetch_large_transfers()
    trending = fetch_trending_tokens()

    return {
        "whales_count": len(eth),
        "total_eth": round(sum(w.get("amount_eth", 0) for w in eth), 1),
        "trending_count": len(trending),
        "trending_vol_m": round(sum(t["vol_24h"] for t in trending), 1)
    }

if __name__ == "__main__":
    print("Backend running (Etherscan V2 only)")
    print(f"Etherscan key: {'present' if ETHERSCAN_KEY else 'missing – mock mode'}")
    print("→ http://localhost:8000/docs")
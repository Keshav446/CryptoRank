import os
import random
from datetime import datetime
from typing import List, Dict, Any

import requests
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel


import google.generativeai as genai
import os

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

GEMINI_KEY = os.getenv("GEMINI_API_KEY")

if GEMINI_KEY:
    genai.configure(api_key=GEMINI_KEY)

# ===================== INIT =====================




genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

def generate_ai_insight(whales):

    if not whales:
        return "No whale data available"

    try:
        model = genai.GenerativeModel("gemini-1.5-flash")

        prompt = f"""
        Analyze these Ethereum whale transactions and give a short market insight.

        {whales[:5]}

        Explain the possible market impact in 1 sentence.
        """

        response = model.generate_content(prompt)

        return response.text

    except Exception as e:
        print("Gemini error:", e)
        return "AI insight unavailable"
    

load_dotenv()

app = FastAPI(
    title="ONCHAIN AI – Intelligence Agent (Etherscan V2)",
    description="Ethereum whale data via Etherscan V2 API",
    version="1.0"
)

# CORS (allow frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===================== CONFIG =====================

ETHERSCAN_KEY = os.getenv("ETHERSCAN_API_KEY")
ETHERSCAN_BASE = "https://api.etherscan.io/v2/api"

# ===================== RESPONSE MODEL =====================

class DataResponse(BaseModel):
    data: List[Dict]
    metrics: Dict
    source: str
    chart_data: Any | None = None


# ===================== MOCK / ETHERSCAN DATA =====================

def fetch_large_transfers():

    # If no API key → return mock data
    if not ETHERSCAN_KEY:
        return [
            {"wallet": "0x742d35Cc6634C0532925a3b8D9f6E4c9a9f3a9f3", "amount_eth": 142.8, "time": "2m ago", "tx": "0x8f3a..."},
            {"wallet": "0x1a2b3c4d5e6f...", "amount_eth": 89.4, "time": "7m ago", "tx": "0x4d2c..."},
            {"wallet": "0x9f8e7d6c5b4a...", "amount_eth": 312.7, "time": "14m ago", "tx": "0x9a1b..."},
        ]

    try:
        params = {
            "chainid": "1",
            "module": "account",
            "action": "txlist",
            "address": "0x742d35Cc6634C0532925a3b844Bc454e4438f44e",
            "sort": "desc",
            "apikey": ETHERSCAN_KEY,
            "page": 1,
            "offset": 50
        }

        r = requests.get(ETHERSCAN_BASE, params=params, timeout=10)
        data = r.json()

        txs = data.get("result", [])

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

        return result

    except Exception as e:
        print("Etherscan fetch error:", e)
        return []


def fetch_trending_tokens():

    try:

        r = requests.get(
            "https://api.dexscreener.com/latest/dex/search?q=eth",
            timeout=10
        )

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
        return []


# ===================== ROUTES =====================

@app.get("/")
def home():
    return {"message": "AI Agent API Running 🚀"}



@app.get("/whales")
@app.get("/whales-eth")
def get_whales():

    raw = fetch_large_transfers()

    total = sum(w.get("amount_eth", 0) for w in raw)

    metrics = {
        "count": len(raw),
        "total_eth": round(total, 1),
        "avg_eth": round(total / max(1, len(raw)), 1)
    }

    chart_data = [
        {"hour": h, "count": random.randint(5, 45)}
        for h in range(24)
    ]

    insight = "Whale activity detected. Large ETH transfers may indicate institutional accumulation."

    return {
    "data": raw,
    "metrics": metrics,
    "source": "Ethereum (Etherscan V2)",
    "chart_data": chart_data,
    "ai_insight": insight
    }

@app.get("/whales")
def get_whales():

    whales = fetch_large_transfers()

    insight = generate_ai_insight(whales)

    return {
        "data": whales,
        "ai_insight": insight
    }


@app.get("/trending", response_model=DataResponse)
def get_trending():

    raw = fetch_trending_tokens()

    total_vol = sum(t["vol_24h"] for t in raw)

    metrics = {
        "count": len(raw),
        "total_vol_m": round(total_vol, 1),
    }

    chart_data = [
        {"token": t["token"], "volume_m": t["vol_24h"]}
        for t in raw
    ]

    return DataResponse(
        data=raw,
        metrics=metrics,
        source="DexScreener",
        chart_data=chart_data
    )


@app.get("/pump-signals")
def pump_signals():

    tokens = fetch_trending_tokens()

    signals = []

    for t in tokens:

        if t.get("change_24h", 0) > 5:
            signals.append({
                "token": t["token"],
                "symbol": t["symbol"],
                "price": t["price_usd"],
                "change": t["change_24h"],
                "volume": t["vol_24h"]
            })

    # demo fallback if nothing detected
    if not signals:
        signals = [
            {
                "token": "GROK",
                "symbol": "GROK",
                "price": 0.00018,
                "change": 34.2,
                "volume": 120
            }
        ]

    analysis = f"{len(signals)} tokens showing abnormal price increase. Possible pump activity."

    return {
        "data": signals,
        "metrics": {"active_signals": len(signals)},
        "ai_analysis": analysis
    }


@app.get("/airdrops")
def get_airdrops():
    return {
        "data": [
            {
                "project": "ZKsync",
                "token": "ZK",
                "eligibility": "Bridge + Swap",
                "reward": "$450",
                "status": "Likely"
            },
            {
                "project": "LayerZero",
                "token": "ZRO",
                "eligibility": "Cross-chain activity",
                "reward": "$320",
                "status": "Confirmed"
            },
            {
                "project": "Scroll",
                "token": "SCR",
                "eligibility": "Testnet participation",
                "reward": "$150",
                "status": "Potential"
            }
        ],
        "metrics": {
            "airdrops_found": 3
        }
    }




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
"""NLN-connected Solana quote comparison and DEX arbitrage candidate scanner."""

from __future__ import annotations

import json
import os
import urllib.request
import uuid
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Quote:
    venue: str
    base_mint: str
    quote_mint: str
    bid: float
    ask: float
    fee_bps: float = 0.0
    observed_slot: int = 0


class NlnRpc:
    """Minimal JSON-RPC client for an NLN Solana endpoint."""

    def __init__(self, url: str | None = None, timeout: int = 15):
        self.url = url or os.environ["NLN_RPC_URL"]
        self.timeout = timeout

    def call(self, method: str, params: list[Any] | None = None) -> Any:
        body = json.dumps({"jsonrpc": "2.0", "id": str(uuid.uuid4()), "method": method, "params": params or []}).encode()
        request = urllib.request.Request(self.url, data=body, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(request, timeout=self.timeout) as response:
            result = json.load(response)
        if result.get("error"):
            raise RuntimeError(f"NLN RPC error: {result['error']}")
        return result["result"]

    def current_slot(self) -> int:
        """Confirm NLN RPC connectivity and return the node's current slot."""
        return int(self.call("getSlot", [{"commitment": "confirmed"}]))


def scan_arbitrage(quotes: list[Quote], trade_size: float = 1.0, min_edge_bps: float = 0.0) -> list[dict[str, Any]]:
    """Compare every compatible buy/sell pair and return net candidates."""
    opportunities = []
    for buy in quotes:
        for sell in quotes:
            if buy.venue == sell.venue or (buy.base_mint, buy.quote_mint) != (sell.base_mint, sell.quote_mint):
                continue
            if sell.bid <= buy.ask:
                continue
            gross_edge_bps = (sell.bid / buy.ask - 1) * 10_000
            net_edge_bps = gross_edge_bps - buy.fee_bps - sell.fee_bps
            if net_edge_bps < min_edge_bps:
                continue
            opportunities.append({"buy_venue": buy.venue, "sell_venue": sell.venue, "buy_price": buy.ask, "sell_price": sell.bid, "gross_edge_bps": round(gross_edge_bps, 4), "net_edge_bps": round(net_edge_bps, 4), "estimated_profit_quote": round(trade_size * (sell.bid - buy.ask) - trade_size * buy.ask * (buy.fee_bps + sell.fee_bps) / 10_000, 8), "observed_slot": max(buy.observed_slot, sell.observed_slot), "confidence": 0.0})
    return sorted(opportunities, key=lambda item: item["net_edge_bps"], reverse=True)


def load_quotes(path: str) -> list[Quote]:
    with open(path, encoding="utf-8") as stream:
        rows = json.load(stream)
    return [Quote(**row) for row in rows]

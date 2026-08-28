#!/usr/bin/env python3
"""Validate normalized DEX quotes and show the current NLN Solana slot."""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from arbitrage_scanner import NlnRpc, load_quotes  # noqa: E402

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("quotes", help="JSON file containing normalized DEX quotes")
args = parser.parse_args()

quotes = load_quotes(args.quotes)
slot = NlnRpc().current_slot()
print(json.dumps({"nln_rpc": "connected", "current_slot": slot, "quote_count": len(quotes)}, indent=2))
for quote in quotes:
    print(json.dumps({"venue": quote.venue, "pair": f"{quote.base_mint}/{quote.quote_mint}", "bid": quote.bid, "ask": quote.ask, "observed_slot": quote.observed_slot}))

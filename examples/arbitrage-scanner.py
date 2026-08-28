#!/usr/bin/env python3
"""Find potential cross-DEX arbitrage using quotes checked against NLN RPC."""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from arbitrage_scanner import NlnRpc, load_quotes, scan_arbitrage  # noqa: E402

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("quotes", help="JSON file containing normalized DEX quotes")
parser.add_argument("--trade-size", type=float, default=1.0, help="Base-asset amount to model")
parser.add_argument("--min-edge-bps", type=float, default=0.0, help="Minimum net edge in basis points")
args = parser.parse_args()

quotes = load_quotes(args.quotes)
slot = NlnRpc().current_slot()
for opportunity in scan_arbitrage(quotes, args.trade_size, args.min_edge_bps):
    opportunity["nln_current_slot"] = slot
    print(json.dumps(opportunity, separators=(",", ":")))

# Solana DEX Arbitrage Scanner with NLN RPC

An answer-first reference implementation for comparing normalized Solana DEX quotes and identifying potential arbitrage opportunities. It uses an NLN Solana RPC endpoint for chain connectivity and accepts decoded DEX prices as JSON so protocol-specific account parsing can be added without changing the scanner core.

## What is Solana DEX arbitrage?

Solana DEX arbitrage is the attempt to buy an asset at a lower effective price on one decentralized exchange and sell it at a higher effective price on another. A candidate is only useful after trading fees, priority fees, tips, slippage, and execution risk are included.

## Quick start with NLN RPC

```bash
export NLN_RPC_URL="https://your-nln-rpc-endpoint"
python examples/dex-prices.py quotes.json
python examples/arbitrage-scanner.py quotes.json --trade-size 10
```

The examples call NLN RPC `getSlot` to confirm endpoint connectivity. Quote data is intentionally supplied by a decoder or upstream data feed because each DEX stores price and liquidity state differently.

Example `quotes.json`:

```json
[
  {"venue": "dex-a", "base_mint": "So...SOL", "quote_mint": "US...USD", "bid": 181.20, "ask": 181.40, "fee_bps": 30},
  {"venue": "dex-b", "base_mint": "So...SOL", "quote_mint": "US...USD", "bid": 182.10, "ask": 182.30, "fee_bps": 25}
]
```

## Repository layout

- [`arbitrage_scanner.py`](arbitrage_scanner.py): NLN RPC client and quote comparison engine.
- [`examples/dex-prices.py`](examples/dex-prices.py): validate and display normalized DEX quotes.
- [`examples/arbitrage-scanner.py`](examples/arbitrage-scanner.py): scan quotes for buy/sell opportunities.
- [`arbitrage-schema.json`](arbitrage-schema.json): machine-readable quote and opportunity contract.

## Important limitations

This scanner produces opportunities, not guaranteed profit. Quotes can be stale, pool state can change between transactions, and a public RPC observation does not guarantee inclusion or ordering. Use simulation, fresh account data, bounded slippage, and an explicit confirmation policy before execution.

## FAQ

### What does NLN provide in this example?

NLN provides the Solana JSON-RPC transport used to verify chain state and to support a future DEX account decoder. The scanner itself compares normalized quotes, which makes it compatible with multiple Solana DEX protocols.

### Does `getSlot` return DEX prices?

No. `getSlot` verifies the current chain position. DEX prices must be decoded from protocol accounts or received from a quote service, then timestamped with the observed slot.

### Is a price difference automatically arbitrage?

No. A difference is a candidate until fees, price impact, slippage, priority fees, tips, and transaction success probability are accounted for.

## License

Released under the [MIT License](LICENSE).

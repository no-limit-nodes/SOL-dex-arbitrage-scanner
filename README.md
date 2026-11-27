<h1 align="center">Solana DEX Arbitrage Scanner: Compare DEX Quotes and Net Out Fees</h1>

<p align="center">
  <b>Feed in normalized quotes from any Solana DEX, get back buy/sell arbitrage candidates ranked by net edge after trading fees.</b><br>
  <sub>An answer-first Python reference implementation: a quote comparison engine, a minimal JSON-RPC client for a <a href="https://nolimitnodes.com">NoLimitNodes</a> Solana RPC endpoint, two runnable examples, and a JSON Schema for quotes and opportunities.</sub>
</p>

<p align="center">
  <a href="./LICENSE"><img alt="MIT License" src="https://img.shields.io/badge/license-MIT-lightgrey?style=flat-square"></a>
  <a href="#quickstart-scan-quotes-for-arbitrage"><img alt="Python 3" src="https://img.shields.io/badge/python-3-blue?style=flat-square"></a>
  <a href="#repo-layout"><img alt="No dependencies" src="https://img.shields.io/badge/dependencies-stdlib%20only-green?style=flat-square"></a>
  <a href="https://nolimitnodes.com"><img alt="Powered by NoLimitNodes" src="https://img.shields.io/badge/powered%20by-NoLimitNodes-FBDE00?style=flat-square&labelColor=000000"></a>
  <a href="#how-it-works"><img alt="JSON-RPC" src="https://img.shields.io/badge/transport-JSON--RPC-brightgreen?style=flat-square"></a>
  <a href="https://solana.com"><img alt="Solana Mainnet" src="https://img.shields.io/badge/solana-mainnet-9945FF?style=flat-square"></a>
</p>

<p align="center">
  <a href="#quickstart-scan-quotes-for-arbitrage">Quickstart</a> ·
  <a href="#quote-format">Quote format</a> ·
  <a href="#how-the-net-edge-is-calculated">Net edge</a> ·
  <a href="#important-limitations">Limitations</a> ·
  <a href="#use-cases">Use cases</a> ·
  <a href="#faq">FAQ</a>
</p>

---

## What this is

A **Solana DEX arbitrage scanner** in a 65-line Python module. It compares normalized quotes for the same token pair across decentralized exchanges and flags pairs where one venue's bid is above another venue's ask, then subtracts both venues' trading fees to report a net edge in basis points and an estimated profit for a given trade size.

It uses a NoLimitNodes Solana RPC endpoint for chain connectivity (`getSlot`) and accepts decoded DEX prices as JSON, so protocol-specific account parsing can be added without changing the scanner core.

> **This scanner produces candidates, not guaranteed profit.** It is a reference implementation, not a trading bot, and nothing here is financial advice. Read [Important limitations](#important-limitations) before using any output to trade.

**If you've been looking for any of these, you're in the right place:**

- A **Solana arbitrage scanner in Python** with no third-party packages
- A **cross-DEX price comparison** for Raydium, Orca, Meteora or any venue you can decode
- How to **calculate arbitrage net edge in basis points** after DEX fees
- A **JSON Schema for DEX quotes and arbitrage opportunities**
- A minimal **Solana JSON-RPC client** for `getSlot`
- A starting point for a **Solana arbitrage bot** quote engine

### What is Solana DEX arbitrage?

Solana DEX arbitrage is the attempt to buy an asset at a lower effective price on one decentralized exchange and sell it at a higher effective price on another. A candidate is only useful after trading fees, priority fees, tips, slippage, and execution risk are included.

## Who this is for

- **Arbitrage bot developers** who need a small, readable quote-comparison core to build on
- **Quant and data teams** screening decoded DEX prices for cross-venue spreads
- **Solana developers learning arbitrage** who want to see the fee arithmetic in plain code

## Quickstart: scan quotes for arbitrage

### Step 1. Get an RPC endpoint

Head to **[app.nolimitnodes.com/register](https://app.nolimitnodes.com/register)** and create an account. You get a 5-day free trial of the Pro plan, no credit card required. Copy your Solana RPC endpoint URL from the dashboard.

### Step 2. Clone and run

```bash
git clone https://github.com/no-limit-nodes/SOL-dex-arbitrage-scanner.git
cd SOL-dex-arbitrage-scanner
export NLN_RPC_URL="https://your-nln-rpc-endpoint"

python examples/dex-prices.py quotes.json
python examples/arbitrage-scanner.py quotes.json --trade-size 10
```

The examples call NLN RPC `getSlot` (at `confirmed` commitment) to confirm endpoint connectivity. Quote data is intentionally supplied by a decoder or upstream data feed because each DEX stores price and liquidity state differently. You create `quotes.json` yourself; it is not shipped in the repo.

Example `quotes.json`:

```json
[
  {"venue": "dex-a", "base_mint": "So...SOL", "quote_mint": "US...USD", "bid": 181.20, "ask": 181.40, "fee_bps": 30},
  {"venue": "dex-b", "base_mint": "So...SOL", "quote_mint": "US...USD", "bid": 182.10, "ask": 182.30, "fee_bps": 25}
]
```

`examples/dex-prices.py` prints a connectivity summary (`nln_rpc`, `current_slot`, `quote_count`), then one line per quote with `venue`, `pair`, `bid`, `ask` and `observed_slot`.

`examples/arbitrage-scanner.py` prints one JSON line per candidate. **With the sample quotes above it prints nothing**, and that is the point of the example: buying on `dex-a` at 181.40 and selling on `dex-b` at 182.10 is a 38.59 bps gross edge, but the two venues charge 30 + 25 = 55 bps, so the net edge is -16.41 bps. Lower the threshold to see the rejected candidate:

```bash
python examples/arbitrage-scanner.py quotes.json --trade-size 10 --min-edge-bps -20
```

```text
{"buy_venue":"dex-a","sell_venue":"dex-b","buy_price":181.4,"sell_price":182.1,"gross_edge_bps":38.5888,"net_edge_bps":-16.4112,"estimated_profit_quote":-2.977,"observed_slot":0,"confidence":0.0,"nln_current_slot":<current slot>}
```

### Script options

| Script | Argument | Default | Meaning |
|---|---|---|---|
| `examples/dex-prices.py` | `quotes` | required | JSON file containing normalized DEX quotes |
| `examples/arbitrage-scanner.py` | `quotes` | required | JSON file containing normalized DEX quotes |
| `examples/arbitrage-scanner.py` | `--trade-size` | `1.0` | Base-asset amount to model |
| `examples/arbitrage-scanner.py` | `--min-edge-bps` | `0.0` | Minimum net edge in basis points |

| Environment variable | Used by | Meaning |
|---|---|---|
| `NLN_RPC_URL` | `NlnRpc` in `arbitrage_scanner.py` | Solana JSON-RPC endpoint URL. Required by both examples. |

## Quote format

`load_quotes()` reads a JSON array and builds one `Quote` per object:

| Field | Type | Required by the loader | Meaning |
|---|---|---|---|
| `venue` | string | yes | DEX or pool label. Quotes from the same venue are never paired. |
| `base_mint` | string | yes | Base token mint |
| `quote_mint` | string | yes | Quote token mint |
| `bid` | number | yes | Price you can sell at |
| `ask` | number | yes | Price you can buy at |
| `fee_bps` | number | no (default `0`) | Venue trading fee in basis points |
| `observed_slot` | integer | no (default `0`) | Slot at which the quote was observed |

[`arbitrage-schema.json`](arbitrage-schema.json) is the machine-readable contract. It defines two shapes: a **DEX quote** (requires `venue`, `base_mint`, `quote_mint`, `bid`, `ask`, `observed_slot`; also lists optional `pool`, `fee_bps` and `source`, default `"nln-rpc"`) and an **arbitrage opportunity** (requires `buy_venue`, `sell_venue`, `net_edge_bps`, `observed_slot`; also `buy_price`, `sell_price`, `gross_edge_bps`, `estimated_profit_quote`, `confidence` from 0 to 1).

> Note: the loader passes each object straight to the `Quote` dataclass, so extra keys such as `pool` or `source` raise a `TypeError`. Strip them before calling `load_quotes()`, or extend `Quote`.

## How the net edge is calculated

For every pair of quotes with the same `(base_mint, quote_mint)` on different venues, where `sell.bid > buy.ask`:

```text
gross_edge_bps         = (sell.bid / buy.ask - 1) * 10_000
net_edge_bps           = gross_edge_bps - buy.fee_bps - sell.fee_bps
estimated_profit_quote = trade_size * (sell.bid - buy.ask)
                         - trade_size * buy.ask * (buy.fee_bps + sell.fee_bps) / 10_000
observed_slot          = max(buy.observed_slot, sell.observed_slot)
```

Candidates with `net_edge_bps` below `--min-edge-bps` are dropped. The rest are sorted by `net_edge_bps`, highest first. `confidence` is always `0.0` in this reference version; it is a placeholder for your own scoring. Priority fees, tips, slippage and price impact are **not** subtracted.

## Important limitations

This scanner produces opportunities, not guaranteed profit. Quotes can be stale, pool state can change between transactions, and a public RPC observation does not guarantee inclusion or ordering. Use simulation, fresh account data, bounded slippage, and an explicit confirmation policy before execution.

- Fees are the only cost modelled. Priority fees, tips, slippage and price impact are left to you.
- Quotes are treated as fixed prices with no depth, so `--trade-size` scales profit linearly.
- `getSlot` checks connectivity and chain position only. It does not fetch or validate prices.
- Only two-venue, same-pair opportunities are checked. Triangular or multi-hop routes are out of scope.

## Use cases

- **Prototype an arbitrage engine.** Plug your own Raydium, Orca or Meteora decoder output into `scan_arbitrage()` and iterate on thresholds.
- **Screen spreads offline.** Run recorded quote snapshots through the scanner to see how often a gross spread survives fees.
- **Teach the fee math.** The sample quotes show a positive gross spread that turns negative after fees.
- **Standardize a data contract.** Use `arbitrage-schema.json` as the interface between a quote decoder and downstream consumers.

## How it works

`NlnRpc` sends a JSON-RPC 2.0 POST to `NLN_RPC_URL` with Python's `urllib` (15 s timeout) and raises on any RPC error. `current_slot()` calls `getSlot` with `confirmed` commitment. `scan_arbitrage()` compares every buy/sell combination of the loaded quotes, applies the formulas above, and returns the candidates as dictionaries. `examples/arbitrage-scanner.py` adds the current slot as `nln_current_slot` to each candidate and prints it as one JSON line.

## Repo layout

```
.
├── arbitrage_scanner.py       # NLN RPC client and quote comparison engine
├── arbitrage-schema.json      # machine-readable quote and opportunity contract
├── examples/
│   ├── dex-prices.py          # validate and display normalized DEX quotes
│   └── arbitrage-scanner.py   # scan quotes for buy/sell opportunities
├── LICENSE                    # MIT
└── README.md
```

## FAQ

<details>
<summary><b>What does NLN provide in this example?</b></summary>

NLN provides the Solana JSON-RPC transport used to verify chain state and to support a future DEX account decoder. The scanner itself compares normalized quotes, which makes it compatible with multiple Solana DEX protocols. Set `NLN_RPC_URL` to your endpoint and both examples call `getSlot` before printing anything.
</details>

<details>
<summary><b>Does <code>getSlot</code> return DEX prices?</b></summary>

No. `getSlot` verifies the current chain position. DEX prices must be decoded from protocol accounts or received from a quote service, then timestamped with the observed slot. This repo leaves that decoding step to you and expects the result in `quotes.json`, one object per venue and pair.
</details>

<details>
<summary><b>Is a price difference automatically arbitrage?</b></summary>

No. A difference is a candidate until fees, price impact, slippage, priority fees, tips, and transaction success probability are accounted for. The bundled sample shows this: a 38.59 bps gross spread becomes -16.41 bps once 55 bps of combined trading fees are subtracted, so the scanner reports nothing.
</details>

<details>
<summary><b>How do I calculate Solana arbitrage profit in basis points?</b></summary>

Divide the sell venue's bid by the buy venue's ask, subtract one, and multiply by 10,000 for the gross edge. Then subtract each venue's fee in basis points to get the net edge. This scanner does exactly that, and estimates profit in the quote token for a chosen `--trade-size`.
</details>

<details>
<summary><b>Why does the arbitrage scanner print nothing?</b></summary>

Every candidate's net edge is below `--min-edge-bps`, which defaults to `0.0`. Either the spreads do not cover fees, the quotes are for different mint pairs, or all quotes share one venue. Pass a negative threshold, for example `--min-edge-bps -20`, to inspect the candidates that were rejected.
</details>

<details>
<summary><b>Can this scanner execute trades on Solana?</b></summary>

No. It only reads quotes and calls `getSlot`. It does not build, simulate, sign or send transactions. To act on a candidate you need fresh account data, simulation, bounded slippage, priority fees or tips, and a confirmation policy, all of which sit outside this reference implementation.
</details>

## Learn more on NoLimitNodes Academy

- [Solana AMM pool types: Raydium, Orca, Meteora, PumpSwap](https://nolimitnodes.com/academy/solana-amm-pool-types-raydium-orca-meteora-pumpswap). Why each DEX stores price state differently, which is why quotes arrive pre-decoded here.
- [What is a Solana RPC node?](https://nolimitnodes.com/academy/what-is-a-solana-rpc-node) Background on the endpoint behind `NLN_RPC_URL`.
- [Send Solana transactions that land](https://nolimitnodes.com/academy/send-solana-transactions-that-land). The execution step this scanner leaves out.
- [Ways to get real-time Solana data, compared](https://nolimitnodes.com/academy/ways-to-get-real-time-solana-data-compared). Options for feeding fresh quotes into the scanner.

## Contributing

Issues and pull requests are welcome, for example DEX decoders that emit the quote format above.

## License

Released under the [MIT License](LICENSE).

## Related resources

- [NoLimitNodes: Solana RPC and streaming infrastructure](https://nolimitnodes.com)
- [NoLimitNodes Solana RPC nodes](https://nolimitnodes.com/products/rpc-nodes)
- [NoLimitNodes RPC quickstart](https://nolimitnodes.com/docs/quickstarts/rpc)
- [NoLimitNodes Solana RPC API reference](https://nolimitnodes.com/docs/api-reference/solana-rpc/overview)
- [Triangular arbitrage (glossary)](https://nolimitnodes.com/glossary/triangular-arbitrage)
- [Solana arbitrage bot development](https://nolimitnodes.com/custom-development/solana-arbitrage-bot-development)
- [Solana `getSlot` RPC method](https://solana.com/docs/rpc/http/getslot)
- [Raydium](https://raydium.io) · [Orca](https://www.orca.so) · [Meteora](https://www.meteora.ag)

---

<p align="center">
  <b>Ready to scan Solana DEX quotes for arbitrage?</b><br>
  <a href="https://app.nolimitnodes.com/register">Register, get a 5-day free Pro trial, grab your RPC endpoint →</a>
</p>

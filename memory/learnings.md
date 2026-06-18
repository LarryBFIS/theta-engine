# Engine learnings — realized edge by bucket

_Generated 2026-06-18T17:53:16.244585+00:00 · from the outcomes ledger. Buckets act on the scanner only at n ≥ 20 closes (shrunk toward the global prior). Below that they're shown but inert (×1.00)._

**Global: 31 closed · win rate 32% · realized $-3793.50**

## asset_class

| value | n | win rate | shrunk | avg P&L | total | ×mult | call |
|---|---:|---:|---:|---:|---:|---:|---|
| index_etf | 12 | 58% | 46% | $+12 | $+145 | ×1.00 | watch (n=12 < 20) |
| sector_etf | 1 | 0% | 29% | $-418 | $-418 | ×1.00 | watch (n=1 < 20) |
| single_name | 18 | 17% | 22% | $-196 | $-3520 | ×1.00 | watch (n=18 < 20) |

## structure

| value | n | win rate | shrunk | avg P&L | total | ×mult | call |
|---|---:|---:|---:|---:|---:|---:|---|
| short_put_vertical | 21 | 48% | 43% | $-49 | $-1024 | ×1.32 | favor |
| iron_condor | 6 | 0% | 20% | $-197 | $-1182 | ×1.00 | watch (n=6 < 20) |
| short_call_vertical | 4 | 0% | 23% | $-397 | $-1588 | ×1.00 | watch (n=4 < 20) |

## cluster

| value | n | win rate | shrunk | avg P&L | total | ×mult | call |
|---|---:|---:|---:|---:|---:|---:|---|
| us_index | 6 | 100% | 58% | $+107 | $+642 | ×1.00 | watch (n=6 < 20) |
| metals | 1 | 0% | 29% | $-418 | $-418 | ×1.00 | watch (n=1 < 20) |
| energy | 1 | 0% | 29% | $-538 | $-538 | ×1.00 | watch (n=1 < 20) |
| financials | 1 | 0% | 29% | $-850 | $-850 | ×1.00 | watch (n=1 < 20) |
| us_tech | 22 | 18% | 23% | $-120 | $-2630 | ×0.70 | AVOID (neg expectancy; wr 23% < prior 32%) |

## size

| value | n | win rate | shrunk | avg P&L | total | ×mult | call |
|---|---:|---:|---:|---:|---:|---:|---|
| 2x | 14 | 43% | 38% | $-33 | $-466 | ×1.00 | watch (n=14 < 20) |
| 3x | 5 | 40% | 35% | $-95 | $-476 | ×1.00 | watch (n=5 < 20) |
| 4x | 12 | 17% | 24% | $-238 | $-2852 | ×1.00 | watch (n=12 < 20) |


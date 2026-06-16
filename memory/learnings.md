# Engine learnings — realized edge by bucket

_Generated 2026-06-16T17:26:26.269330+00:00 · from the outcomes ledger. Buckets act on the scanner only at n ≥ 20 closes (shrunk toward the global prior). Below that they're shown but inert (×1.00)._

**Global: 30 closed · win rate 33% · realized $-3420.00**

## asset_class

| value | n | win rate | shrunk | avg P&L | total | ×mult | call |
|---|---:|---:|---:|---:|---:|---:|---|
| index_etf | 12 | 58% | 47% | $+12 | $+145 | ×1.00 | watch (n=12 < 20) |
| sector_etf | 1 | 0% | 30% | $-418 | $-418 | ×1.00 | watch (n=1 < 20) |
| single_name | 17 | 18% | 24% | $-185 | $-3147 | ×1.00 | watch (n=17 < 20) |

## structure

| value | n | win rate | shrunk | avg P&L | total | ×mult | call |
|---|---:|---:|---:|---:|---:|---:|---|
| short_put_vertical | 20 | 50% | 44% | $-32 | $-650 | ×1.33 | favor |
| iron_condor | 6 | 0% | 21% | $-197 | $-1182 | ×1.00 | watch (n=6 < 20) |
| short_call_vertical | 4 | 0% | 24% | $-397 | $-1588 | ×1.00 | watch (n=4 < 20) |

## cluster

| value | n | win rate | shrunk | avg P&L | total | ×mult | call |
|---|---:|---:|---:|---:|---:|---:|---|
| us_index | 6 | 100% | 58% | $+107 | $+642 | ×1.00 | watch (n=6 < 20) |
| metals | 1 | 0% | 30% | $-418 | $-418 | ×1.00 | watch (n=1 < 20) |
| energy | 1 | 0% | 30% | $-538 | $-538 | ×1.00 | watch (n=1 < 20) |
| financials | 1 | 0% | 30% | $-850 | $-850 | ×1.00 | watch (n=1 < 20) |
| us_tech | 21 | 19% | 24% | $-107 | $-2256 | ×0.71 | AVOID (neg expectancy; wr 24% < prior 33%) |

## size

| value | n | win rate | shrunk | avg P&L | total | ×mult | call |
|---|---:|---:|---:|---:|---:|---:|---|
| 3x | 4 | 50% | 38% | $-26 | $-102 | ×1.00 | watch (n=4 < 20) |
| 2x | 14 | 43% | 39% | $-33 | $-466 | ×1.00 | watch (n=14 < 20) |
| 4x | 12 | 17% | 24% | $-238 | $-2852 | ×1.00 | watch (n=12 < 20) |


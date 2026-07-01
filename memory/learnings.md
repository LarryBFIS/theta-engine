# Engine learnings — realized edge by bucket

_Generated 2026-07-01T16:14:36.481843+00:00 · from the outcomes ledger. Buckets act on the scanner only at n ≥ 20 closes (shrunk toward the global prior). Below that they're shown but inert (×1.00)._

**Global: 52 closed · win rate 29% · realized $-8616.50**

## asset_class

| value | n | win rate | shrunk | avg P&L | total | ×mult | call |
|---|---:|---:|---:|---:|---:|---:|---|
| index_etf | 16 | 56% | 46% | $+9 | $+140 | ×1.00 | watch (n=16 < 20) |
| sector_etf | 1 | 0% | 26% | $-418 | $-418 | ×1.00 | watch (n=1 < 20) |
| single_name | 35 | 17% | 20% | $-238 | $-8338 | ×0.68 | AVOID (neg expectancy; wr 20% < prior 29%) |

## structure

| value | n | win rate | shrunk | avg P&L | total | ×mult | call |
|---|---:|---:|---:|---:|---:|---:|---|
| iron_condor | 6 | 0% | 18% | $-197 | $-1182 | ×1.00 | watch (n=6 < 20) |
| short_put_vertical | 33 | 42% | 39% | $-84 | $-2774 | ×1.36 | favor |
| short_call_vertical | 13 | 8% | 17% | $-358 | $-4660 | ×1.00 | watch (n=13 < 20) |

## cluster

| value | n | win rate | shrunk | avg P&L | total | ×mult | call |
|---|---:|---:|---:|---:|---:|---:|---|
| us_index | 9 | 89% | 57% | $+92 | $+832 | ×1.00 | watch (n=9 < 20) |
| consumer | 1 | 0% | 26% | $-385 | $-385 | ×1.00 | watch (n=1 < 20) |
| metals | 1 | 0% | 26% | $-418 | $-418 | ×1.00 | watch (n=1 < 20) |
| financials | 2 | 0% | 24% | $-549 | $-1098 | ×1.00 | watch (n=2 < 20) |
| industrials | 3 | 0% | 22% | $-392 | $-1177 | ×1.00 | watch (n=3 < 20) |
| energy | 5 | 20% | 26% | $-320 | $-1602 | ×1.00 | watch (n=5 < 20) |
| us_tech | 31 | 19% | 22% | $-154 | $-4768 | ×0.75 | AVOID (neg expectancy; wr 22% < prior 29%) |

## size

| value | n | win rate | shrunk | avg P&L | total | ×mult | call |
|---|---:|---:|---:|---:|---:|---:|---|
| 1x | 2 | 50% | 32% | $-76 | $-152 | ×1.00 | watch (n=2 < 20) |
| 2x | 21 | 43% | 38% | $-64 | $-1347 | ×1.33 | favor |
| 4x | 14 | 21% | 24% | $-225 | $-3156 | ×1.00 | watch (n=14 < 20) |
| 3x | 15 | 13% | 20% | $-264 | $-3962 | ×1.00 | watch (n=15 < 20) |


# Engine learnings — realized edge by bucket

_Generated 2026-06-30T17:54:20.785388+00:00 · from the outcomes ledger. Buckets act on the scanner only at n ≥ 20 closes (shrunk toward the global prior). Below that they're shown but inert (×1.00)._

**Global: 49 closed · win rate 31% · realized $-7445.50**

## asset_class

| value | n | win rate | shrunk | avg P&L | total | ×mult | call |
|---|---:|---:|---:|---:|---:|---:|---|
| index_etf | 16 | 56% | 46% | $+9 | $+140 | ×1.00 | watch (n=16 < 20) |
| sector_etf | 1 | 0% | 28% | $-418 | $-418 | ×1.00 | watch (n=1 < 20) |
| single_name | 32 | 19% | 22% | $-224 | $-7167 | ×0.70 | AVOID (neg expectancy; wr 22% < prior 31%) |

## structure

| value | n | win rate | shrunk | avg P&L | total | ×mult | call |
|---|---:|---:|---:|---:|---:|---:|---|
| iron_condor | 6 | 0% | 19% | $-197 | $-1182 | ×1.00 | watch (n=6 < 20) |
| short_put_vertical | 32 | 44% | 41% | $-78 | $-2482 | ×1.33 | favor |
| short_call_vertical | 11 | 9% | 19% | $-344 | $-3782 | ×1.00 | watch (n=11 < 20) |

## cluster

| value | n | win rate | shrunk | avg P&L | total | ×mult | call |
|---|---:|---:|---:|---:|---:|---:|---|
| us_index | 9 | 89% | 58% | $+92 | $+832 | ×1.00 | watch (n=9 < 20) |
| consumer | 1 | 0% | 28% | $-385 | $-385 | ×1.00 | watch (n=1 < 20) |
| metals | 1 | 0% | 28% | $-418 | $-418 | ×1.00 | watch (n=1 < 20) |
| industrials | 2 | 0% | 26% | $-366 | $-732 | ×1.00 | watch (n=2 < 20) |
| financials | 2 | 0% | 26% | $-549 | $-1098 | ×1.00 | watch (n=2 < 20) |
| energy | 4 | 25% | 29% | $-292 | $-1169 | ×1.00 | watch (n=4 < 20) |
| us_tech | 30 | 20% | 23% | $-149 | $-4476 | ×0.74 | AVOID (neg expectancy; wr 23% < prior 31%) |

## size

| value | n | win rate | shrunk | avg P&L | total | ×mult | call |
|---|---:|---:|---:|---:|---:|---:|---|
| 1x | 2 | 50% | 34% | $-76 | $-152 | ×1.00 | watch (n=2 < 20) |
| 2x | 20 | 45% | 40% | $-45 | $-902 | ×1.31 | favor |
| 4x | 14 | 21% | 25% | $-225 | $-3156 | ×1.00 | watch (n=14 < 20) |
| 3x | 13 | 15% | 22% | $-249 | $-3236 | ×1.00 | watch (n=13 < 20) |


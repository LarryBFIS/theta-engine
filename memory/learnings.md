# Engine learnings — realized edge by bucket

_Generated 2026-06-29T18:54:15.402120+00:00 · from the outcomes ledger. Buckets act on the scanner only at n ≥ 20 closes (shrunk toward the global prior). Below that they're shown but inert (×1.00)._

**Global: 45 closed · win rate 29% · realized $-7126.50**

## asset_class

| value | n | win rate | shrunk | avg P&L | total | ×mult | call |
|---|---:|---:|---:|---:|---:|---:|---|
| index_etf | 15 | 53% | 44% | $+3 | $+46 | ×1.00 | watch (n=15 < 20) |
| sector_etf | 1 | 0% | 26% | $-418 | $-418 | ×1.00 | watch (n=1 < 20) |
| single_name | 29 | 17% | 20% | $-233 | $-6755 | ×0.70 | AVOID (neg expectancy; wr 20% < prior 29%) |

## structure

| value | n | win rate | shrunk | avg P&L | total | ×mult | call |
|---|---:|---:|---:|---:|---:|---:|---|
| iron_condor | 6 | 0% | 18% | $-197 | $-1182 | ×1.00 | watch (n=6 < 20) |
| short_put_vertical | 29 | 41% | 38% | $-83 | $-2407 | ×1.32 | favor |
| short_call_vertical | 10 | 10% | 19% | $-354 | $-3538 | ×1.00 | watch (n=10 < 20) |

## cluster

| value | n | win rate | shrunk | avg P&L | total | ×mult | call |
|---|---:|---:|---:|---:|---:|---:|---|
| us_index | 8 | 88% | 55% | $+92 | $+739 | ×1.00 | watch (n=8 < 20) |
| consumer | 1 | 0% | 26% | $-385 | $-385 | ×1.00 | watch (n=1 < 20) |
| metals | 1 | 0% | 26% | $-418 | $-418 | ×1.00 | watch (n=1 < 20) |
| industrials | 2 | 0% | 24% | $-366 | $-732 | ×1.00 | watch (n=2 < 20) |
| energy | 3 | 33% | 30% | $-308 | $-924 | ×1.00 | watch (n=3 < 20) |
| financials | 2 | 0% | 24% | $-549 | $-1098 | ×1.00 | watch (n=2 < 20) |
| us_tech | 28 | 18% | 21% | $-154 | $-4308 | ×0.72 | AVOID (neg expectancy; wr 21% < prior 29%) |

## size

| value | n | win rate | shrunk | avg P&L | total | ×mult | call |
|---|---:|---:|---:|---:|---:|---:|---|
| 1x | 2 | 50% | 32% | $-76 | $-152 | ×1.00 | watch (n=2 < 20) |
| 2x | 18 | 39% | 35% | $-62 | $-1120 | ×1.00 | watch (n=18 < 20) |
| 3x | 11 | 18% | 23% | $-245 | $-2698 | ×1.00 | watch (n=11 < 20) |
| 4x | 14 | 21% | 24% | $-225 | $-3156 | ×1.00 | watch (n=14 < 20) |


# Engine learnings — realized edge by bucket

_Generated 2026-11-25T14:15:16.427668+00:00 · from the outcomes ledger. Buckets act on the scanner only at n ≥ 20 closes (shrunk toward the global prior). Below that they're shown but inert (×1.00)._

**Global: 109 closed · win rate 38% · realized $-12688.00**

## asset_class

| value | n | win rate | shrunk | avg P&L | total | ×mult | call |
|---|---:|---:|---:|---:|---:|---:|---|
| index_etf | 49 | 55% | 52% | $-7 | $-348 | ×1.39 | favor |
| sector_etf | 5 | 20% | 32% | $-125 | $-626 | ×1.00 | watch (n=5 < 20) |
| single_name | 55 | 24% | 26% | $-213 | $-11714 | ×0.69 | AVOID (neg expectancy; wr 26% < prior 38%) |

## structure

| value | n | win rate | shrunk | avg P&L | total | ×mult | call |
|---|---:|---:|---:|---:|---:|---:|---|
| iron_condor | 8 | 12% | 26% | $-150 | $-1203 | ×1.00 | watch (n=8 < 20) |
| short_put_vertical | 72 | 46% | 45% | $-58 | $-4154 | ×1.19 | favor |
| short_call_vertical | 29 | 24% | 28% | $-253 | $-7330 | ×0.73 | AVOID (neg expectancy; wr 28% < prior 38%) |

## cluster

| value | n | win rate | shrunk | avg P&L | total | ×mult | call |
|---|---:|---:|---:|---:|---:|---:|---|
| us_index | 42 | 62% | 57% | $+8 | $+344 | ×1.50 | favor |
| healthcare | 2 | 0% | 31% | $-96 | $-191 | ×1.00 | watch (n=2 < 20) |
| metals | 2 | 50% | 40% | $-184 | $-368 | ×1.00 | watch (n=2 < 20) |
| consumer | 2 | 0% | 31% | $-298 | $-596 | ×1.00 | watch (n=2 < 20) |
| financials | 2 | 0% | 31% | $-549 | $-1098 | ×1.00 | watch (n=2 < 20) |
| industrials | 3 | 0% | 29% | $-392 | $-1177 | ×1.00 | watch (n=3 < 20) |
| energy | 7 | 14% | 28% | $-262 | $-1834 | ×1.00 | watch (n=7 < 20) |
| us_tech | 49 | 26% | 28% | $-159 | $-7768 | ×0.76 | AVOID (neg expectancy; wr 28% < prior 38%) |

## size

| value | n | win rate | shrunk | avg P&L | total | ×mult | call |
|---|---:|---:|---:|---:|---:|---:|---|
| 2x | 23 | 39% | 39% | $-70 | $-1617 | ×1.03 | neutral |
| 4x | 14 | 21% | 28% | $-225 | $-3156 | ×1.00 | watch (n=14 < 20) |
| 3x | 17 | 24% | 29% | $-225 | $-3826 | ×1.00 | watch (n=17 < 20) |
| 1x | 55 | 46% | 44% | $-74 | $-4088 | ×1.18 | favor |


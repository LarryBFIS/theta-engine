# Engine learnings — realized edge by bucket

_Generated 2026-11-24T15:45:23.297892+00:00 · from the outcomes ledger. Buckets act on the scanner only at n ≥ 20 closes (shrunk toward the global prior). Below that they're shown but inert (×1.00)._

**Global: 107 closed · win rate 38% · realized $-12302.00**

## asset_class

| value | n | win rate | shrunk | avg P&L | total | ×mult | call |
|---|---:|---:|---:|---:|---:|---:|---|
| index_etf | 48 | 56% | 53% | $-4 | $-213 | ×1.39 | favor |
| sector_etf | 5 | 20% | 32% | $-125 | $-626 | ×1.00 | watch (n=5 < 20) |
| single_name | 54 | 24% | 26% | $-212 | $-11463 | ×0.69 | AVOID (neg expectancy; wr 26% < prior 38%) |

## structure

| value | n | win rate | shrunk | avg P&L | total | ×mult | call |
|---|---:|---:|---:|---:|---:|---:|---|
| iron_condor | 8 | 12% | 27% | $-150 | $-1203 | ×1.00 | watch (n=8 < 20) |
| short_put_vertical | 71 | 46% | 46% | $-57 | $-4019 | ×1.19 | favor |
| short_call_vertical | 28 | 25% | 28% | $-253 | $-7080 | ×0.74 | AVOID (neg expectancy; wr 29% < prior 38%) |

## cluster

| value | n | win rate | shrunk | avg P&L | total | ×mult | call |
|---|---:|---:|---:|---:|---:|---:|---|
| us_index | 41 | 63% | 58% | $+12 | $+480 | ×1.50 | favor |
| healthcare | 2 | 0% | 32% | $-96 | $-191 | ×1.00 | watch (n=2 < 20) |
| metals | 2 | 50% | 40% | $-184 | $-368 | ×1.00 | watch (n=2 < 20) |
| consumer | 2 | 0% | 32% | $-298 | $-596 | ×1.00 | watch (n=2 < 20) |
| financials | 2 | 0% | 32% | $-549 | $-1098 | ×1.00 | watch (n=2 < 20) |
| industrials | 3 | 0% | 30% | $-392 | $-1177 | ×1.00 | watch (n=3 < 20) |
| energy | 7 | 14% | 28% | $-262 | $-1834 | ×1.00 | watch (n=7 < 20) |
| us_tech | 48 | 27% | 29% | $-157 | $-7518 | ×0.76 | AVOID (neg expectancy; wr 29% < prior 38%) |

## size

| value | n | win rate | shrunk | avg P&L | total | ×mult | call |
|---|---:|---:|---:|---:|---:|---:|---|
| 2x | 23 | 39% | 39% | $-70 | $-1617 | ×1.01 | neutral |
| 4x | 14 | 21% | 28% | $-225 | $-3156 | ×1.00 | watch (n=14 < 20) |
| 1x | 53 | 47% | 46% | $-70 | $-3702 | ×1.19 | favor |
| 3x | 17 | 24% | 29% | $-225 | $-3826 | ×1.00 | watch (n=17 < 20) |


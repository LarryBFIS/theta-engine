# Engine learnings — realized edge by bucket

_Generated 2026-10-08T19:15:08.004001+00:00 · from the outcomes ledger. Buckets act on the scanner only at n ≥ 20 closes (shrunk toward the global prior). Below that they're shown but inert (×1.00)._

**Global: 84 closed · win rate 42% · realized $-9156.00**

## asset_class

| value | n | win rate | shrunk | avg P&L | total | ×mult | call |
|---|---:|---:|---:|---:|---:|---:|---|
| index_etf | 35 | 63% | 58% | $+11 | $+376 | ×1.40 | favor |
| sector_etf | 4 | 25% | 37% | $-130 | $-518 | ×1.00 | watch (n=4 < 20) |
| single_name | 45 | 27% | 29% | $-200 | $-9013 | ×0.70 | AVOID (neg expectancy; wr 29% < prior 42%) |

## structure

| value | n | win rate | shrunk | avg P&L | total | ×mult | call |
|---|---:|---:|---:|---:|---:|---:|---|
| iron_condor | 7 | 14% | 30% | $-162 | $-1136 | ×1.00 | watch (n=7 < 20) |
| short_put_vertical | 59 | 51% | 50% | $-47 | $-2755 | ×1.19 | favor |
| short_call_vertical | 18 | 22% | 29% | $-292 | $-5265 | ×1.00 | watch (n=18 < 20) |

## cluster

| value | n | win rate | shrunk | avg P&L | total | ×mult | call |
|---|---:|---:|---:|---:|---:|---:|---|
| us_index | 28 | 75% | 66% | $+38 | $+1068 | ×1.50 | favor |
| healthcare | 1 | 0% | 38% | $-84 | $-84 | ×1.00 | watch (n=1 < 20) |
| metals | 2 | 50% | 43% | $-184 | $-368 | ×1.00 | watch (n=2 < 20) |
| consumer | 2 | 0% | 35% | $-298 | $-596 | ×1.00 | watch (n=2 < 20) |
| financials | 2 | 0% | 35% | $-549 | $-1098 | ×1.00 | watch (n=2 < 20) |
| industrials | 3 | 0% | 32% | $-392 | $-1177 | ×1.00 | watch (n=3 < 20) |
| energy | 7 | 14% | 30% | $-262 | $-1834 | ×1.00 | watch (n=7 < 20) |
| us_tech | 39 | 31% | 33% | $-130 | $-5068 | ×0.79 | AVOID (neg expectancy; wr 33% < prior 42%) |

## size

| value | n | win rate | shrunk | avg P&L | total | ×mult | call |
|---|---:|---:|---:|---:|---:|---:|---|
| 1x | 30 | 63% | 58% | $-19 | $-556 | ×1.39 | favor |
| 2x | 23 | 39% | 40% | $-70 | $-1617 | ×0.96 | AVOID (neg expectancy; wr 40% < prior 42%) |
| 4x | 14 | 21% | 30% | $-225 | $-3156 | ×1.00 | watch (n=14 < 20) |
| 3x | 17 | 24% | 30% | $-225 | $-3826 | ×1.00 | watch (n=17 < 20) |


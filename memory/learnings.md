# Engine learnings — realized edge by bucket

_Generated 2026-10-14T17:57:47.313419+00:00 · from the outcomes ledger. Buckets act on the scanner only at n ≥ 20 closes (shrunk toward the global prior). Below that they're shown but inert (×1.00)._

**Global: 86 closed · win rate 42% · realized $-9121.00**

## asset_class

| value | n | win rate | shrunk | avg P&L | total | ×mult | call |
|---|---:|---:|---:|---:|---:|---:|---|
| index_etf | 37 | 62% | 58% | $+11 | $+410 | ×1.38 | favor |
| sector_etf | 4 | 25% | 37% | $-130 | $-518 | ×1.00 | watch (n=4 < 20) |
| single_name | 45 | 27% | 29% | $-200 | $-9013 | ×0.70 | AVOID (neg expectancy; wr 29% < prior 42%) |

## structure

| value | n | win rate | shrunk | avg P&L | total | ×mult | call |
|---|---:|---:|---:|---:|---:|---:|---|
| iron_condor | 7 | 14% | 30% | $-162 | $-1136 | ×1.00 | watch (n=7 < 20) |
| short_put_vertical | 59 | 51% | 50% | $-47 | $-2755 | ×1.18 | favor |
| short_call_vertical | 20 | 25% | 31% | $-262 | $-5230 | ×0.73 | AVOID (neg expectancy; wr 31% < prior 42%) |

## cluster

| value | n | win rate | shrunk | avg P&L | total | ×mult | call |
|---|---:|---:|---:|---:|---:|---:|---|
| us_index | 30 | 73% | 66% | $+37 | $+1103 | ×1.50 | favor |
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
| 1x | 32 | 62% | 58% | $-16 | $-522 | ×1.38 | favor |
| 2x | 23 | 39% | 40% | $-70 | $-1617 | ×0.95 | AVOID (neg expectancy; wr 40% < prior 42%) |
| 4x | 14 | 21% | 30% | $-225 | $-3156 | ×1.00 | watch (n=14 < 20) |
| 3x | 17 | 24% | 30% | $-225 | $-3826 | ×1.00 | watch (n=17 < 20) |


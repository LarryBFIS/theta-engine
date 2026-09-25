# Engine learnings — realized edge by bucket

_Generated 2026-09-25T16:51:09.575605+00:00 · from the outcomes ledger. Buckets act on the scanner only at n ≥ 20 closes (shrunk toward the global prior). Below that they're shown but inert (×1.00)._

**Global: 80 closed · win rate 39% · realized $-9311.00**

## asset_class

| value | n | win rate | shrunk | avg P&L | total | ×mult | call |
|---|---:|---:|---:|---:|---:|---:|---|
| index_etf | 32 | 59% | 55% | $+8 | $+251 | ×1.41 | favor |
| sector_etf | 4 | 25% | 35% | $-130 | $-518 | ×1.00 | watch (n=4 < 20) |
| single_name | 44 | 25% | 28% | $-206 | $-9044 | ×0.71 | AVOID (neg expectancy; wr 28% < prior 39%) |

## structure

| value | n | win rate | shrunk | avg P&L | total | ×mult | call |
|---|---:|---:|---:|---:|---:|---:|---|
| iron_condor | 7 | 14% | 29% | $-162 | $-1136 | ×1.00 | watch (n=7 < 20) |
| short_put_vertical | 57 | 49% | 48% | $-50 | $-2841 | ×1.23 | favor |
| short_call_vertical | 16 | 12% | 23% | $-333 | $-5334 | ×1.00 | watch (n=16 < 20) |

## cluster

| value | n | win rate | shrunk | avg P&L | total | ×mult | call |
|---|---:|---:|---:|---:|---:|---:|---|
| us_index | 25 | 72% | 62% | $+38 | $+944 | ×1.50 | favor |
| healthcare | 1 | 0% | 35% | $-84 | $-84 | ×1.00 | watch (n=1 < 20) |
| metals | 2 | 50% | 41% | $-184 | $-368 | ×1.00 | watch (n=2 < 20) |
| consumer | 2 | 0% | 32% | $-298 | $-596 | ×1.00 | watch (n=2 < 20) |
| financials | 2 | 0% | 32% | $-549 | $-1098 | ×1.00 | watch (n=2 < 20) |
| industrials | 3 | 0% | 30% | $-392 | $-1177 | ×1.00 | watch (n=3 < 20) |
| energy | 7 | 14% | 29% | $-262 | $-1834 | ×1.00 | watch (n=7 < 20) |
| us_tech | 38 | 29% | 31% | $-134 | $-5098 | ×0.80 | AVOID (neg expectancy; wr 31% < prior 39%) |

## size

| value | n | win rate | shrunk | avg P&L | total | ×mult | call |
|---|---:|---:|---:|---:|---:|---:|---|
| 1x | 26 | 58% | 52% | $-27 | $-712 | ×1.35 | favor |
| 2x | 23 | 39% | 39% | $-70 | $-1617 | ×1.01 | neutral |
| 4x | 14 | 21% | 29% | $-225 | $-3156 | ×1.00 | watch (n=14 < 20) |
| 3x | 17 | 24% | 29% | $-225 | $-3826 | ×1.00 | watch (n=17 < 20) |


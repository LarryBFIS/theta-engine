# Engine learnings — realized edge by bucket

_Generated 2026-08-12T17:27:10.522254+00:00 · from the outcomes ledger. Buckets act on the scanner only at n ≥ 20 closes (shrunk toward the global prior). Below that they're shown but inert (×1.00)._

**Global: 65 closed · win rate 35% · realized $-9194.00**

## asset_class

| value | n | win rate | shrunk | avg P&L | total | ×mult | call |
|---|---:|---:|---:|---:|---:|---:|---|
| index_etf | 22 | 59% | 52% | $+11 | $+238 | ×1.46 | favor |
| sector_etf | 2 | 50% | 38% | $-184 | $-368 | ×1.00 | watch (n=2 < 20) |
| single_name | 41 | 22% | 25% | $-221 | $-9064 | ×0.69 | AVOID (neg expectancy; wr 25% < prior 35%) |

## structure

| value | n | win rate | shrunk | avg P&L | total | ×mult | call |
|---|---:|---:|---:|---:|---:|---:|---|
| iron_condor | 6 | 0% | 22% | $-197 | $-1182 | ×1.00 | watch (n=6 < 20) |
| short_put_vertical | 43 | 49% | 46% | $-62 | $-2678 | ×1.31 | favor |
| short_call_vertical | 16 | 12% | 21% | $-333 | $-5334 | ×1.00 | watch (n=16 < 20) |

## cluster

| value | n | win rate | shrunk | avg P&L | total | ×mult | call |
|---|---:|---:|---:|---:|---:|---:|---|
| us_index | 15 | 80% | 62% | $+62 | $+930 | ×1.00 | watch (n=15 < 20) |
| metals | 2 | 50% | 38% | $-184 | $-368 | ×1.00 | watch (n=2 < 20) |
| consumer | 2 | 0% | 30% | $-298 | $-596 | ×1.00 | watch (n=2 < 20) |
| financials | 2 | 0% | 30% | $-549 | $-1098 | ×1.00 | watch (n=2 < 20) |
| industrials | 3 | 0% | 27% | $-392 | $-1177 | ×1.00 | watch (n=3 < 20) |
| energy | 6 | 17% | 28% | $-295 | $-1768 | ×1.00 | watch (n=6 < 20) |
| us_tech | 35 | 26% | 28% | $-146 | $-5118 | ×0.79 | AVOID (neg expectancy; wr 28% < prior 35%) |

## size

| value | n | win rate | shrunk | avg P&L | total | ×mult | call |
|---|---:|---:|---:|---:|---:|---:|---|
| 1x | 11 | 64% | 50% | $-54 | $-594 | ×1.00 | watch (n=11 < 20) |
| 2x | 23 | 39% | 38% | $-70 | $-1617 | ×1.07 | favor |
| 4x | 14 | 21% | 27% | $-225 | $-3156 | ×1.00 | watch (n=14 < 20) |
| 3x | 17 | 24% | 28% | $-225 | $-3826 | ×1.00 | watch (n=17 < 20) |


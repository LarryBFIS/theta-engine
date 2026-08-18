# Engine learnings — realized edge by bucket

_Generated 2026-08-18T20:12:42.679575+00:00 · from the outcomes ledger. Buckets act on the scanner only at n ≥ 20 closes (shrunk toward the global prior). Below that they're shown but inert (×1.00)._

**Global: 67 closed · win rate 36% · realized $-9181.00**

## asset_class

| value | n | win rate | shrunk | avg P&L | total | ×mult | call |
|---|---:|---:|---:|---:|---:|---:|---|
| index_etf | 24 | 58% | 52% | $+10 | $+251 | ×1.44 | favor |
| sector_etf | 2 | 50% | 38% | $-184 | $-368 | ×1.00 | watch (n=2 < 20) |
| single_name | 41 | 22% | 25% | $-221 | $-9064 | ×0.69 | AVOID (neg expectancy; wr 25% < prior 36%) |

## structure

| value | n | win rate | shrunk | avg P&L | total | ×mult | call |
|---|---:|---:|---:|---:|---:|---:|---|
| iron_condor | 6 | 0% | 22% | $-197 | $-1182 | ×1.00 | watch (n=6 < 20) |
| short_put_vertical | 45 | 49% | 46% | $-59 | $-2665 | ×1.30 | favor |
| short_call_vertical | 16 | 12% | 22% | $-333 | $-5334 | ×1.00 | watch (n=16 < 20) |

## cluster

| value | n | win rate | shrunk | avg P&L | total | ×mult | call |
|---|---:|---:|---:|---:|---:|---:|---|
| us_index | 17 | 76% | 61% | $+56 | $+944 | ×1.00 | watch (n=17 < 20) |
| metals | 2 | 50% | 38% | $-184 | $-368 | ×1.00 | watch (n=2 < 20) |
| consumer | 2 | 0% | 30% | $-298 | $-596 | ×1.00 | watch (n=2 < 20) |
| financials | 2 | 0% | 30% | $-549 | $-1098 | ×1.00 | watch (n=2 < 20) |
| industrials | 3 | 0% | 28% | $-392 | $-1177 | ×1.00 | watch (n=3 < 20) |
| energy | 6 | 17% | 29% | $-295 | $-1768 | ×1.00 | watch (n=6 < 20) |
| us_tech | 35 | 26% | 28% | $-146 | $-5118 | ×0.78 | AVOID (neg expectancy; wr 28% < prior 36%) |

## size

| value | n | win rate | shrunk | avg P&L | total | ×mult | call |
|---|---:|---:|---:|---:|---:|---:|---|
| 1x | 13 | 62% | 50% | $-45 | $-582 | ×1.00 | watch (n=13 < 20) |
| 2x | 23 | 39% | 38% | $-70 | $-1617 | ×1.06 | favor |
| 4x | 14 | 21% | 27% | $-225 | $-3156 | ×1.00 | watch (n=14 < 20) |
| 3x | 17 | 24% | 28% | $-225 | $-3826 | ×1.00 | watch (n=17 < 20) |


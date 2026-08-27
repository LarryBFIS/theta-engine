# Engine learnings — realized edge by bucket

_Generated 2026-08-27T15:30:39.462007+00:00 · from the outcomes ledger. Buckets act on the scanner only at n ≥ 20 closes (shrunk toward the global prior). Below that they're shown but inert (×1.00)._

**Global: 68 closed · win rate 35% · realized $-9250.50**

## asset_class

| value | n | win rate | shrunk | avg P&L | total | ×mult | call |
|---|---:|---:|---:|---:|---:|---:|---|
| index_etf | 24 | 58% | 52% | $+10 | $+251 | ×1.46 | favor |
| sector_etf | 2 | 50% | 38% | $-184 | $-368 | ×1.00 | watch (n=2 < 20) |
| single_name | 42 | 21% | 24% | $-217 | $-9133 | ×0.68 | AVOID (neg expectancy; wr 24% < prior 35%) |

## structure

| value | n | win rate | shrunk | avg P&L | total | ×mult | call |
|---|---:|---:|---:|---:|---:|---:|---|
| iron_condor | 6 | 0% | 22% | $-197 | $-1182 | ×1.00 | watch (n=6 < 20) |
| short_put_vertical | 46 | 48% | 46% | $-59 | $-2734 | ×1.29 | favor |
| short_call_vertical | 16 | 12% | 21% | $-333 | $-5334 | ×1.00 | watch (n=16 < 20) |

## cluster

| value | n | win rate | shrunk | avg P&L | total | ×mult | call |
|---|---:|---:|---:|---:|---:|---:|---|
| us_index | 17 | 76% | 61% | $+56 | $+944 | ×1.00 | watch (n=17 < 20) |
| metals | 2 | 50% | 38% | $-184 | $-368 | ×1.00 | watch (n=2 < 20) |
| consumer | 2 | 0% | 29% | $-298 | $-596 | ×1.00 | watch (n=2 < 20) |
| financials | 2 | 0% | 29% | $-549 | $-1098 | ×1.00 | watch (n=2 < 20) |
| industrials | 3 | 0% | 27% | $-392 | $-1177 | ×1.00 | watch (n=3 < 20) |
| energy | 6 | 17% | 28% | $-295 | $-1768 | ×1.00 | watch (n=6 < 20) |
| us_tech | 36 | 25% | 27% | $-144 | $-5188 | ×0.77 | AVOID (neg expectancy; wr 27% < prior 35%) |

## size

| value | n | win rate | shrunk | avg P&L | total | ×mult | call |
|---|---:|---:|---:|---:|---:|---:|---|
| 1x | 14 | 57% | 48% | $-46 | $-651 | ×1.00 | watch (n=14 < 20) |
| 2x | 23 | 39% | 38% | $-70 | $-1617 | ×1.08 | favor |
| 4x | 14 | 21% | 27% | $-225 | $-3156 | ×1.00 | watch (n=14 < 20) |
| 3x | 17 | 24% | 28% | $-225 | $-3826 | ×1.00 | watch (n=17 < 20) |


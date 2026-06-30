# Engine learnings — realized edge by bucket

_Generated 2026-06-30T13:24:58.000271+00:00 · from the outcomes ledger. Buckets act on the scanner only at n ≥ 20 closes (shrunk toward the global prior). Below that they're shown but inert (×1.00)._

**Global: 46 closed · win rate 28% · realized $-7371.00**

## asset_class

| value | n | win rate | shrunk | avg P&L | total | ×mult | call |
|---|---:|---:|---:|---:|---:|---:|---|
| index_etf | 15 | 53% | 43% | $+3 | $+46 | ×1.00 | watch (n=15 < 20) |
| sector_etf | 1 | 0% | 26% | $-418 | $-418 | ×1.00 | watch (n=1 < 20) |
| single_name | 30 | 17% | 20% | $-233 | $-7000 | ×0.69 | AVOID (neg expectancy; wr 20% < prior 28%) |

## structure

| value | n | win rate | shrunk | avg P&L | total | ×mult | call |
|---|---:|---:|---:|---:|---:|---:|---|
| iron_condor | 6 | 0% | 18% | $-197 | $-1182 | ×1.00 | watch (n=6 < 20) |
| short_put_vertical | 29 | 41% | 38% | $-83 | $-2407 | ×1.34 | favor |
| short_call_vertical | 11 | 9% | 18% | $-344 | $-3782 | ×1.00 | watch (n=11 < 20) |

## cluster

| value | n | win rate | shrunk | avg P&L | total | ×mult | call |
|---|---:|---:|---:|---:|---:|---:|---|
| us_index | 8 | 88% | 55% | $+92 | $+739 | ×1.00 | watch (n=8 < 20) |
| consumer | 1 | 0% | 26% | $-385 | $-385 | ×1.00 | watch (n=1 < 20) |
| metals | 1 | 0% | 26% | $-418 | $-418 | ×1.00 | watch (n=1 < 20) |
| industrials | 2 | 0% | 24% | $-366 | $-732 | ×1.00 | watch (n=2 < 20) |
| financials | 2 | 0% | 24% | $-549 | $-1098 | ×1.00 | watch (n=2 < 20) |
| energy | 4 | 25% | 27% | $-292 | $-1169 | ×1.00 | watch (n=4 < 20) |
| us_tech | 28 | 18% | 21% | $-154 | $-4308 | ×0.73 | AVOID (neg expectancy; wr 21% < prior 28%) |

## size

| value | n | win rate | shrunk | avg P&L | total | ×mult | call |
|---|---:|---:|---:|---:|---:|---:|---|
| 1x | 2 | 50% | 32% | $-76 | $-152 | ×1.00 | watch (n=2 < 20) |
| 2x | 18 | 39% | 35% | $-62 | $-1120 | ×1.00 | watch (n=18 < 20) |
| 3x | 12 | 17% | 22% | $-245 | $-2943 | ×1.00 | watch (n=12 < 20) |
| 4x | 14 | 21% | 24% | $-225 | $-3156 | ×1.00 | watch (n=14 < 20) |


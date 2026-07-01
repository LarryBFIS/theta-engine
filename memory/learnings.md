# Engine learnings — realized edge by bucket

_Generated 2026-07-01T13:34:28.205333+00:00 · from the outcomes ledger. Buckets act on the scanner only at n ≥ 20 closes (shrunk toward the global prior). Below that they're shown but inert (×1.00)._

**Global: 50 closed · win rate 30% · realized $-7738.00**

## asset_class

| value | n | win rate | shrunk | avg P&L | total | ×mult | call |
|---|---:|---:|---:|---:|---:|---:|---|
| index_etf | 16 | 56% | 46% | $+9 | $+140 | ×1.00 | watch (n=16 < 20) |
| sector_etf | 1 | 0% | 27% | $-418 | $-418 | ×1.00 | watch (n=1 < 20) |
| single_name | 33 | 18% | 21% | $-226 | $-7460 | ×0.70 | AVOID (neg expectancy; wr 21% < prior 30%) |

## structure

| value | n | win rate | shrunk | avg P&L | total | ×mult | call |
|---|---:|---:|---:|---:|---:|---:|---|
| iron_condor | 6 | 0% | 19% | $-197 | $-1182 | ×1.00 | watch (n=6 < 20) |
| short_put_vertical | 33 | 42% | 40% | $-84 | $-2774 | ×1.32 | favor |
| short_call_vertical | 11 | 9% | 19% | $-344 | $-3782 | ×1.00 | watch (n=11 < 20) |

## cluster

| value | n | win rate | shrunk | avg P&L | total | ×mult | call |
|---|---:|---:|---:|---:|---:|---:|---|
| us_index | 9 | 89% | 58% | $+92 | $+832 | ×1.00 | watch (n=9 < 20) |
| consumer | 1 | 0% | 27% | $-385 | $-385 | ×1.00 | watch (n=1 < 20) |
| metals | 1 | 0% | 27% | $-418 | $-418 | ×1.00 | watch (n=1 < 20) |
| industrials | 2 | 0% | 25% | $-366 | $-732 | ×1.00 | watch (n=2 < 20) |
| financials | 2 | 0% | 25% | $-549 | $-1098 | ×1.00 | watch (n=2 < 20) |
| energy | 4 | 25% | 29% | $-292 | $-1169 | ×1.00 | watch (n=4 < 20) |
| us_tech | 31 | 19% | 22% | $-154 | $-4768 | ×0.73 | AVOID (neg expectancy; wr 22% < prior 30%) |

## size

| value | n | win rate | shrunk | avg P&L | total | ×mult | call |
|---|---:|---:|---:|---:|---:|---:|---|
| 1x | 2 | 50% | 33% | $-76 | $-152 | ×1.00 | watch (n=2 < 20) |
| 2x | 20 | 45% | 40% | $-45 | $-902 | ×1.33 | favor |
| 4x | 14 | 21% | 25% | $-225 | $-3156 | ×1.00 | watch (n=14 < 20) |
| 3x | 14 | 14% | 21% | $-252 | $-3528 | ×1.00 | watch (n=14 < 20) |


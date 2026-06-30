# Engine learnings — realized edge by bucket

_Generated 2026-06-30T16:30:34.432774+00:00 · from the outcomes ledger. Buckets act on the scanner only at n ≥ 20 closes (shrunk toward the global prior). Below that they're shown but inert (×1.00)._

**Global: 47 closed · win rate 28% · realized $-7663.50**

## asset_class

| value | n | win rate | shrunk | avg P&L | total | ×mult | call |
|---|---:|---:|---:|---:|---:|---:|---|
| index_etf | 15 | 53% | 43% | $+3 | $+46 | ×1.00 | watch (n=15 < 20) |
| sector_etf | 1 | 0% | 25% | $-418 | $-418 | ×1.00 | watch (n=1 < 20) |
| single_name | 31 | 16% | 19% | $-235 | $-7292 | ×0.69 | AVOID (neg expectancy; wr 19% < prior 28%) |

## structure

| value | n | win rate | shrunk | avg P&L | total | ×mult | call |
|---|---:|---:|---:|---:|---:|---:|---|
| iron_condor | 6 | 0% | 17% | $-197 | $-1182 | ×1.00 | watch (n=6 < 20) |
| short_put_vertical | 30 | 40% | 37% | $-90 | $-2700 | ×1.33 | favor |
| short_call_vertical | 11 | 9% | 18% | $-344 | $-3782 | ×1.00 | watch (n=11 < 20) |

## cluster

| value | n | win rate | shrunk | avg P&L | total | ×mult | call |
|---|---:|---:|---:|---:|---:|---:|---|
| us_index | 8 | 88% | 54% | $+92 | $+739 | ×1.00 | watch (n=8 < 20) |
| consumer | 1 | 0% | 25% | $-385 | $-385 | ×1.00 | watch (n=1 < 20) |
| metals | 1 | 0% | 25% | $-418 | $-418 | ×1.00 | watch (n=1 < 20) |
| industrials | 2 | 0% | 23% | $-366 | $-732 | ×1.00 | watch (n=2 < 20) |
| financials | 2 | 0% | 23% | $-549 | $-1098 | ×1.00 | watch (n=2 < 20) |
| energy | 4 | 25% | 27% | $-292 | $-1169 | ×1.00 | watch (n=4 < 20) |
| us_tech | 29 | 17% | 20% | $-159 | $-4601 | ×0.72 | AVOID (neg expectancy; wr 20% < prior 28%) |

## size

| value | n | win rate | shrunk | avg P&L | total | ×mult | call |
|---|---:|---:|---:|---:|---:|---:|---|
| 1x | 2 | 50% | 31% | $-76 | $-152 | ×1.00 | watch (n=2 < 20) |
| 2x | 18 | 39% | 35% | $-62 | $-1120 | ×1.00 | watch (n=18 < 20) |
| 4x | 14 | 21% | 24% | $-225 | $-3156 | ×1.00 | watch (n=14 < 20) |
| 3x | 13 | 15% | 21% | $-249 | $-3236 | ×1.00 | watch (n=13 < 20) |


# Engine learnings — realized edge by bucket

_Generated 2026-09-22T16:21:35.630849+00:00 · from the outcomes ledger. Buckets act on the scanner only at n ≥ 20 closes (shrunk toward the global prior). Below that they're shown but inert (×1.00)._

**Global: 78 closed · win rate 40% · realized $-9211.00**

## asset_class

| value | n | win rate | shrunk | avg P&L | total | ×mult | call |
|---|---:|---:|---:|---:|---:|---:|---|
| index_etf | 31 | 61% | 56% | $+9 | $+284 | ×1.41 | favor |
| sector_etf | 3 | 33% | 38% | $-151 | $-452 | ×1.00 | watch (n=3 < 20) |
| single_name | 44 | 25% | 28% | $-206 | $-9044 | ×0.70 | AVOID (neg expectancy; wr 28% < prior 40%) |

## structure

| value | n | win rate | shrunk | avg P&L | total | ×mult | call |
|---|---:|---:|---:|---:|---:|---:|---|
| iron_condor | 7 | 14% | 29% | $-162 | $-1136 | ×1.00 | watch (n=7 < 20) |
| short_put_vertical | 55 | 51% | 49% | $-50 | $-2741 | ×1.24 | favor |
| short_call_vertical | 16 | 12% | 23% | $-333 | $-5334 | ×1.00 | watch (n=16 < 20) |

## cluster

| value | n | win rate | shrunk | avg P&L | total | ×mult | call |
|---|---:|---:|---:|---:|---:|---:|---|
| us_index | 24 | 75% | 65% | $+41 | $+977 | ×1.50 | favor |
| healthcare | 1 | 0% | 36% | $-84 | $-84 | ×1.00 | watch (n=1 < 20) |
| metals | 2 | 50% | 42% | $-184 | $-368 | ×1.00 | watch (n=2 < 20) |
| consumer | 2 | 0% | 33% | $-298 | $-596 | ×1.00 | watch (n=2 < 20) |
| financials | 2 | 0% | 33% | $-549 | $-1098 | ×1.00 | watch (n=2 < 20) |
| industrials | 3 | 0% | 31% | $-392 | $-1177 | ×1.00 | watch (n=3 < 20) |
| energy | 6 | 17% | 31% | $-295 | $-1768 | ×1.00 | watch (n=6 < 20) |
| us_tech | 38 | 29% | 31% | $-134 | $-5098 | ×0.79 | AVOID (neg expectancy; wr 31% < prior 40%) |

## size

| value | n | win rate | shrunk | avg P&L | total | ×mult | call |
|---|---:|---:|---:|---:|---:|---:|---|
| 1x | 24 | 62% | 56% | $-25 | $-612 | ×1.40 | favor |
| 2x | 23 | 39% | 39% | $-70 | $-1617 | ×0.99 | AVOID (neg expectancy; wr 39% < prior 40%) |
| 4x | 14 | 21% | 29% | $-225 | $-3156 | ×1.00 | watch (n=14 < 20) |
| 3x | 17 | 24% | 30% | $-225 | $-3826 | ×1.00 | watch (n=17 < 20) |


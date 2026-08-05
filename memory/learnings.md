# Engine learnings — realized edge by bucket

_Generated 2026-08-05T17:14:14.967673+00:00 · from the outcomes ledger. Buckets act on the scanner only at n ≥ 20 closes (shrunk toward the global prior). Below that they're shown but inert (×1.00)._

**Global: 64 closed · win rate 34% · realized $-9249.50**

## asset_class

| value | n | win rate | shrunk | avg P&L | total | ×mult | call |
|---|---:|---:|---:|---:|---:|---:|---|
| index_etf | 22 | 59% | 51% | $+11 | $+238 | ×1.49 | favor |
| sector_etf | 2 | 50% | 37% | $-184 | $-368 | ×1.00 | watch (n=2 < 20) |
| single_name | 40 | 20% | 23% | $-228 | $-9119 | ×0.67 | AVOID (neg expectancy; wr 23% < prior 34%) |

## structure

| value | n | win rate | shrunk | avg P&L | total | ×mult | call |
|---|---:|---:|---:|---:|---:|---:|---|
| iron_condor | 6 | 0% | 22% | $-197 | $-1182 | ×1.00 | watch (n=6 < 20) |
| short_put_vertical | 42 | 48% | 45% | $-65 | $-2734 | ×1.31 | favor |
| short_call_vertical | 16 | 12% | 21% | $-333 | $-5334 | ×1.00 | watch (n=16 < 20) |

## cluster

| value | n | win rate | shrunk | avg P&L | total | ×mult | call |
|---|---:|---:|---:|---:|---:|---:|---|
| us_index | 15 | 80% | 62% | $+62 | $+930 | ×1.00 | watch (n=15 < 20) |
| metals | 2 | 50% | 37% | $-184 | $-368 | ×1.00 | watch (n=2 < 20) |
| consumer | 2 | 0% | 29% | $-298 | $-596 | ×1.00 | watch (n=2 < 20) |
| financials | 2 | 0% | 29% | $-549 | $-1098 | ×1.00 | watch (n=2 < 20) |
| industrials | 3 | 0% | 26% | $-392 | $-1177 | ×1.00 | watch (n=3 < 20) |
| energy | 6 | 17% | 28% | $-295 | $-1768 | ×1.00 | watch (n=6 < 20) |
| us_tech | 34 | 24% | 26% | $-152 | $-5174 | ×0.76 | AVOID (neg expectancy; wr 26% < prior 34%) |

## size

| value | n | win rate | shrunk | avg P&L | total | ×mult | call |
|---|---:|---:|---:|---:|---:|---:|---|
| 1x | 10 | 60% | 47% | $-65 | $-650 | ×1.00 | watch (n=10 < 20) |
| 2x | 23 | 39% | 38% | $-70 | $-1617 | ×1.10 | favor |
| 4x | 14 | 21% | 27% | $-225 | $-3156 | ×1.00 | watch (n=14 < 20) |
| 3x | 17 | 24% | 28% | $-225 | $-3826 | ×1.00 | watch (n=17 < 20) |


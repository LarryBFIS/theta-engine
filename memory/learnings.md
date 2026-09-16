# Engine learnings — realized edge by bucket

_Generated 2026-09-16T19:45:37.868205+00:00 · from the outcomes ledger. Buckets act on the scanner only at n ≥ 20 closes (shrunk toward the global prior). Below that they're shown but inert (×1.00)._

**Global: 75 closed · win rate 37% · realized $-9315.00**

## asset_class

| value | n | win rate | shrunk | avg P&L | total | ×mult | call |
|---|---:|---:|---:|---:|---:|---:|---|
| index_etf | 29 | 59% | 53% | $+8 | $+226 | ×1.42 | favor |
| sector_etf | 3 | 33% | 36% | $-151 | $-452 | ×1.00 | watch (n=3 < 20) |
| single_name | 43 | 23% | 26% | $-211 | $-9090 | ×0.69 | AVOID (neg expectancy; wr 26% < prior 37%) |

## structure

| value | n | win rate | shrunk | avg P&L | total | ×mult | call |
|---|---:|---:|---:|---:|---:|---:|---|
| iron_condor | 6 | 0% | 23% | $-197 | $-1182 | ×1.00 | watch (n=6 < 20) |
| short_put_vertical | 53 | 49% | 47% | $-53 | $-2799 | ×1.26 | favor |
| short_call_vertical | 16 | 12% | 22% | $-333 | $-5334 | ×1.00 | watch (n=16 < 20) |

## cluster

| value | n | win rate | shrunk | avg P&L | total | ×mult | call |
|---|---:|---:|---:|---:|---:|---:|---|
| us_index | 22 | 73% | 62% | $+42 | $+919 | ×1.50 | favor |
| healthcare | 1 | 0% | 34% | $-84 | $-84 | ×1.00 | watch (n=1 < 20) |
| metals | 2 | 50% | 39% | $-184 | $-368 | ×1.00 | watch (n=2 < 20) |
| consumer | 2 | 0% | 31% | $-298 | $-596 | ×1.00 | watch (n=2 < 20) |
| financials | 2 | 0% | 31% | $-549 | $-1098 | ×1.00 | watch (n=2 < 20) |
| industrials | 3 | 0% | 29% | $-392 | $-1177 | ×1.00 | watch (n=3 < 20) |
| energy | 6 | 17% | 30% | $-295 | $-1768 | ×1.00 | watch (n=6 < 20) |
| us_tech | 37 | 27% | 29% | $-139 | $-5144 | ×0.78 | AVOID (neg expectancy; wr 29% < prior 37%) |

## size

| value | n | win rate | shrunk | avg P&L | total | ×mult | call |
|---|---:|---:|---:|---:|---:|---:|---|
| 1x | 21 | 57% | 51% | $-34 | $-716 | ×1.36 | favor |
| 2x | 23 | 39% | 39% | $-70 | $-1617 | ×1.03 | neutral |
| 4x | 14 | 21% | 28% | $-225 | $-3156 | ×1.00 | watch (n=14 < 20) |
| 3x | 17 | 24% | 29% | $-225 | $-3826 | ×1.00 | watch (n=17 < 20) |


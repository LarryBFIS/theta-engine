# Engine learnings — realized edge by bucket

_Generated 2026-07-24T20:37:53.896620+00:00 · from the outcomes ledger. Buckets act on the scanner only at n ≥ 20 closes (shrunk toward the global prior). Below that they're shown but inert (×1.00)._

**Global: 58 closed · win rate 29% · realized $-8969.50**

## asset_class

| value | n | win rate | shrunk | avg P&L | total | ×mult | call |
|---|---:|---:|---:|---:|---:|---:|---|
| index_etf | 19 | 53% | 45% | $+6 | $+112 | ×1.00 | watch (n=19 < 20) |
| sector_etf | 2 | 50% | 33% | $-184 | $-368 | ×1.00 | watch (n=2 < 20) |
| single_name | 37 | 16% | 19% | $-236 | $-8714 | ×0.65 | AVOID (neg expectancy; wr 19% < prior 29%) |

## structure

| value | n | win rate | shrunk | avg P&L | total | ×mult | call |
|---|---:|---:|---:|---:|---:|---:|---|
| iron_condor | 6 | 0% | 18% | $-197 | $-1182 | ×1.00 | watch (n=6 < 20) |
| short_put_vertical | 38 | 42% | 39% | $-77 | $-2916 | ×1.35 | favor |
| short_call_vertical | 14 | 7% | 16% | $-348 | $-4871 | ×1.00 | watch (n=14 < 20) |

## cluster

| value | n | win rate | shrunk | avg P&L | total | ×mult | call |
|---|---:|---:|---:|---:|---:|---:|---|
| us_index | 12 | 75% | 54% | $+67 | $+805 | ×1.00 | watch (n=12 < 20) |
| metals | 2 | 50% | 33% | $-184 | $-368 | ×1.00 | watch (n=2 < 20) |
| consumer | 2 | 0% | 24% | $-298 | $-596 | ×1.00 | watch (n=2 < 20) |
| financials | 2 | 0% | 24% | $-549 | $-1098 | ×1.00 | watch (n=2 < 20) |
| industrials | 3 | 0% | 22% | $-392 | $-1177 | ×1.00 | watch (n=3 < 20) |
| energy | 6 | 17% | 25% | $-295 | $-1768 | ×1.00 | watch (n=6 < 20) |
| us_tech | 31 | 19% | 22% | $-154 | $-4768 | ×0.74 | AVOID (neg expectancy; wr 22% < prior 29%) |

## size

| value | n | win rate | shrunk | avg P&L | total | ×mult | call |
|---|---:|---:|---:|---:|---:|---:|---|
| 1x | 4 | 25% | 28% | $-92 | $-370 | ×1.00 | watch (n=4 < 20) |
| 2x | 23 | 39% | 36% | $-70 | $-1617 | ×1.23 | favor |
| 4x | 14 | 21% | 25% | $-225 | $-3156 | ×1.00 | watch (n=14 < 20) |
| 3x | 17 | 24% | 26% | $-225 | $-3826 | ×1.00 | watch (n=17 < 20) |


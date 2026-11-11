# Engine learnings — realized edge by bucket

_Generated 2026-11-11T19:52:48.769424+00:00 · from the outcomes ledger. Buckets act on the scanner only at n ≥ 20 closes (shrunk toward the global prior). Below that they're shown but inert (×1.00)._

**Global: 93 closed · win rate 41% · realized $-9389.00**

## asset_class

| value | n | win rate | shrunk | avg P&L | total | ×mult | call |
|---|---:|---:|---:|---:|---:|---:|---|
| index_etf | 42 | 60% | 56% | $+8 | $+349 | ×1.37 | favor |
| sector_etf | 4 | 25% | 36% | $-130 | $-518 | ×1.00 | watch (n=4 < 20) |
| single_name | 47 | 26% | 28% | $-196 | $-9220 | ×0.69 | AVOID (neg expectancy; wr 28% < prior 41%) |

## structure

| value | n | win rate | shrunk | avg P&L | total | ×mult | call |
|---|---:|---:|---:|---:|---:|---:|---|
| iron_condor | 8 | 12% | 28% | $-150 | $-1203 | ×1.00 | watch (n=8 < 20) |
| short_put_vertical | 63 | 51% | 49% | $-45 | $-2846 | ×1.21 | favor |
| short_call_vertical | 22 | 23% | 28% | $-243 | $-5340 | ×0.69 | AVOID (neg expectancy; wr 28% < prior 41%) |

## cluster

| value | n | win rate | shrunk | avg P&L | total | ×mult | call |
|---|---:|---:|---:|---:|---:|---:|---|
| us_index | 35 | 69% | 62% | $+30 | $+1042 | ×1.50 | favor |
| healthcare | 1 | 0% | 37% | $-84 | $-84 | ×1.00 | watch (n=1 < 20) |
| metals | 2 | 50% | 42% | $-184 | $-368 | ×1.00 | watch (n=2 < 20) |
| consumer | 2 | 0% | 34% | $-298 | $-596 | ×1.00 | watch (n=2 < 20) |
| financials | 2 | 0% | 34% | $-549 | $-1098 | ×1.00 | watch (n=2 < 20) |
| industrials | 3 | 0% | 31% | $-392 | $-1177 | ×1.00 | watch (n=3 < 20) |
| energy | 7 | 14% | 30% | $-262 | $-1834 | ×1.00 | watch (n=7 < 20) |
| us_tech | 41 | 29% | 32% | $-129 | $-5274 | ×0.77 | AVOID (neg expectancy; wr 32% < prior 41%) |

## size

| value | n | win rate | shrunk | avg P&L | total | ×mult | call |
|---|---:|---:|---:|---:|---:|---:|---|
| 1x | 39 | 56% | 53% | $-20 | $-790 | ×1.30 | favor |
| 2x | 23 | 39% | 40% | $-70 | $-1617 | ×0.97 | AVOID (neg expectancy; wr 40% < prior 41%) |
| 4x | 14 | 21% | 30% | $-225 | $-3156 | ×1.00 | watch (n=14 < 20) |
| 3x | 17 | 24% | 30% | $-225 | $-3826 | ×1.00 | watch (n=17 < 20) |


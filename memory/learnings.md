# Engine learnings — realized edge by bucket

_Generated 2026-10-30T18:32:46.921927+00:00 · from the outcomes ledger. Buckets act on the scanner only at n ≥ 20 closes (shrunk toward the global prior). Below that they're shown but inert (×1.00)._

**Global: 91 closed · win rate 40% · realized $-9494.00**

## asset_class

| value | n | win rate | shrunk | avg P&L | total | ×mult | call |
|---|---:|---:|---:|---:|---:|---:|---|
| index_etf | 40 | 57% | 54% | $+6 | $+244 | ×1.36 | favor |
| sector_etf | 4 | 25% | 35% | $-130 | $-518 | ×1.00 | watch (n=4 < 20) |
| single_name | 47 | 26% | 28% | $-196 | $-9220 | ×0.71 | AVOID (neg expectancy; wr 28% < prior 40%) |

## structure

| value | n | win rate | shrunk | avg P&L | total | ×mult | call |
|---|---:|---:|---:|---:|---:|---:|---|
| iron_condor | 8 | 12% | 28% | $-150 | $-1203 | ×1.00 | watch (n=8 < 20) |
| short_put_vertical | 61 | 49% | 48% | $-48 | $-2951 | ×1.21 | favor |
| short_call_vertical | 22 | 23% | 28% | $-243 | $-5340 | ×0.71 | AVOID (neg expectancy; wr 28% < prior 40%) |

## cluster

| value | n | win rate | shrunk | avg P&L | total | ×mult | call |
|---|---:|---:|---:|---:|---:|---:|---|
| us_index | 33 | 67% | 60% | $+28 | $+936 | ×1.50 | favor |
| healthcare | 1 | 0% | 36% | $-84 | $-84 | ×1.00 | watch (n=1 < 20) |
| metals | 2 | 50% | 41% | $-184 | $-368 | ×1.00 | watch (n=2 < 20) |
| consumer | 2 | 0% | 33% | $-298 | $-596 | ×1.00 | watch (n=2 < 20) |
| financials | 2 | 0% | 33% | $-549 | $-1098 | ×1.00 | watch (n=2 < 20) |
| industrials | 3 | 0% | 30% | $-392 | $-1177 | ×1.00 | watch (n=3 < 20) |
| energy | 7 | 14% | 29% | $-262 | $-1834 | ×1.00 | watch (n=7 < 20) |
| us_tech | 41 | 29% | 31% | $-129 | $-5274 | ×0.79 | AVOID (neg expectancy; wr 31% < prior 40%) |

## size

| value | n | win rate | shrunk | avg P&L | total | ×mult | call |
|---|---:|---:|---:|---:|---:|---:|---|
| 1x | 37 | 54% | 51% | $-24 | $-894 | ×1.29 | favor |
| 2x | 23 | 39% | 39% | $-70 | $-1617 | ×0.99 | AVOID (neg expectancy; wr 39% < prior 40%) |
| 4x | 14 | 21% | 29% | $-225 | $-3156 | ×1.00 | watch (n=14 < 20) |
| 3x | 17 | 24% | 30% | $-225 | $-3826 | ×1.00 | watch (n=17 < 20) |


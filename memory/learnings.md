# Engine learnings — realized edge by bucket

_Generated 2026-11-20T19:45:22.484035+00:00 · from the outcomes ledger. Buckets act on the scanner only at n ≥ 20 closes (shrunk toward the global prior). Below that they're shown but inert (×1.00)._

**Global: 102 closed · win rate 40% · realized $-11259.50**

## asset_class

| value | n | win rate | shrunk | avg P&L | total | ×mult | call |
|---|---:|---:|---:|---:|---:|---:|---|
| index_etf | 45 | 60% | 56% | $+7 | $+334 | ×1.40 | favor |
| sector_etf | 5 | 20% | 34% | $-125 | $-626 | ×1.00 | watch (n=5 < 20) |
| single_name | 52 | 25% | 28% | $-211 | $-10968 | ×0.68 | AVOID (neg expectancy; wr 27% < prior 40%) |

## structure

| value | n | win rate | shrunk | avg P&L | total | ×mult | call |
|---|---:|---:|---:|---:|---:|---:|---|
| iron_condor | 8 | 12% | 28% | $-150 | $-1203 | ×1.00 | watch (n=8 < 20) |
| short_put_vertical | 67 | 49% | 48% | $-49 | $-3267 | ×1.20 | favor |
| short_call_vertical | 27 | 26% | 30% | $-251 | $-6790 | ×0.74 | AVOID (neg expectancy; wr 30% < prior 40%) |

## cluster

| value | n | win rate | shrunk | avg P&L | total | ×mult | call |
|---|---:|---:|---:|---:|---:|---:|---|
| us_index | 38 | 68% | 62% | $+27 | $+1027 | ×1.50 | favor |
| healthcare | 2 | 0% | 34% | $-96 | $-191 | ×1.00 | watch (n=2 < 20) |
| metals | 2 | 50% | 42% | $-184 | $-368 | ×1.00 | watch (n=2 < 20) |
| consumer | 2 | 0% | 34% | $-298 | $-596 | ×1.00 | watch (n=2 < 20) |
| financials | 2 | 0% | 34% | $-549 | $-1098 | ×1.00 | watch (n=2 < 20) |
| industrials | 3 | 0% | 31% | $-392 | $-1177 | ×1.00 | watch (n=3 < 20) |
| energy | 7 | 14% | 30% | $-262 | $-1834 | ×1.00 | watch (n=7 < 20) |
| us_tech | 46 | 28% | 30% | $-153 | $-7023 | ×0.76 | AVOID (neg expectancy; wr 30% < prior 40%) |

## size

| value | n | win rate | shrunk | avg P&L | total | ×mult | call |
|---|---:|---:|---:|---:|---:|---:|---|
| 2x | 23 | 39% | 40% | $-70 | $-1617 | ×0.98 | AVOID (neg expectancy; wr 39% < prior 40%) |
| 1x | 48 | 52% | 50% | $-55 | $-2660 | ×1.25 | favor |
| 4x | 14 | 21% | 29% | $-225 | $-3156 | ×1.00 | watch (n=14 < 20) |
| 3x | 17 | 24% | 30% | $-225 | $-3826 | ×1.00 | watch (n=17 < 20) |


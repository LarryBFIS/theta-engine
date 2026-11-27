# Engine learnings — realized edge by bucket

_Generated 2026-11-27T19:45:21.278451+00:00 · from the outcomes ledger. Buckets act on the scanner only at n ≥ 20 closes (shrunk toward the global prior). Below that they're shown but inert (×1.00)._

**Global: 114 closed · win rate 37% · realized $-13598.00**

## asset_class

| value | n | win rate | shrunk | avg P&L | total | ×mult | call |
|---|---:|---:|---:|---:|---:|---:|---|
| sector_etf | 5 | 20% | 31% | $-125 | $-626 | ×1.00 | watch (n=5 < 20) |
| index_etf | 52 | 54% | 51% | $-12 | $-640 | ×1.39 | favor |
| single_name | 57 | 23% | 25% | $-216 | $-12332 | ×0.68 | AVOID (neg expectancy; wr 25% < prior 37%) |

## structure

| value | n | win rate | shrunk | avg P&L | total | ×mult | call |
|---|---:|---:|---:|---:|---:|---:|---|
| iron_condor | 8 | 12% | 26% | $-150 | $-1203 | ×1.00 | watch (n=8 < 20) |
| short_put_vertical | 76 | 45% | 44% | $-64 | $-4857 | ×1.19 | favor |
| short_call_vertical | 30 | 23% | 27% | $-251 | $-7538 | ×0.72 | AVOID (neg expectancy; wr 27% < prior 37%) |

## cluster

| value | n | win rate | shrunk | avg P&L | total | ×mult | call |
|---|---:|---:|---:|---:|---:|---:|---|
| us_index | 45 | 60% | 56% | $+1 | $+52 | ×1.50 | favor |
| healthcare | 2 | 0% | 31% | $-96 | $-191 | ×1.00 | watch (n=2 < 20) |
| metals | 2 | 50% | 39% | $-184 | $-368 | ×1.00 | watch (n=2 < 20) |
| consumer | 2 | 0% | 31% | $-298 | $-596 | ×1.00 | watch (n=2 < 20) |
| financials | 2 | 0% | 31% | $-549 | $-1098 | ×1.00 | watch (n=2 < 20) |
| industrials | 3 | 0% | 28% | $-392 | $-1177 | ×1.00 | watch (n=3 < 20) |
| energy | 7 | 14% | 28% | $-262 | $-1834 | ×1.00 | watch (n=7 < 20) |
| us_tech | 51 | 26% | 27% | $-164 | $-8387 | ×0.74 | AVOID (neg expectancy; wr 27% < prior 37%) |

## size

| value | n | win rate | shrunk | avg P&L | total | ×mult | call |
|---|---:|---:|---:|---:|---:|---:|---|
| 2x | 24 | 38% | 37% | $-84 | $-2028 | ×1.01 | neutral |
| 4x | 14 | 21% | 28% | $-225 | $-3156 | ×1.00 | watch (n=14 < 20) |
| 3x | 17 | 24% | 28% | $-225 | $-3826 | ×1.00 | watch (n=17 < 20) |
| 1x | 59 | 44% | 43% | $-78 | $-4588 | ×1.17 | favor |


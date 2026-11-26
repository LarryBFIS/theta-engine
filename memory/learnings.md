# Engine learnings — realized edge by bucket

_Generated 2026-11-26T12:48:55.824302+00:00 · from the outcomes ledger. Buckets act on the scanner only at n ≥ 20 closes (shrunk toward the global prior). Below that they're shown but inert (×1.00)._

**Global: 111 closed · win rate 37% · realized $-13236.50**

## asset_class

| value | n | win rate | shrunk | avg P&L | total | ×mult | call |
|---|---:|---:|---:|---:|---:|---:|---|
| index_etf | 50 | 54% | 51% | $-10 | $-486 | ×1.39 | favor |
| sector_etf | 5 | 20% | 31% | $-125 | $-626 | ×1.00 | watch (n=5 < 20) |
| single_name | 56 | 23% | 25% | $-217 | $-12124 | ×0.69 | AVOID (neg expectancy; wr 25% < prior 37%) |

## structure

| value | n | win rate | shrunk | avg P&L | total | ×mult | call |
|---|---:|---:|---:|---:|---:|---:|---|
| iron_condor | 8 | 12% | 26% | $-150 | $-1203 | ×1.00 | watch (n=8 < 20) |
| short_put_vertical | 74 | 45% | 44% | $-64 | $-4703 | ×1.18 | favor |
| short_call_vertical | 29 | 24% | 27% | $-253 | $-7330 | ×0.74 | AVOID (neg expectancy; wr 27% < prior 37%) |

## cluster

| value | n | win rate | shrunk | avg P&L | total | ×mult | call |
|---|---:|---:|---:|---:|---:|---:|---|
| us_index | 43 | 60% | 56% | $+5 | $+206 | ×1.50 | favor |
| healthcare | 2 | 0% | 31% | $-96 | $-191 | ×1.00 | watch (n=2 < 20) |
| metals | 2 | 50% | 39% | $-184 | $-368 | ×1.00 | watch (n=2 < 20) |
| consumer | 2 | 0% | 31% | $-298 | $-596 | ×1.00 | watch (n=2 < 20) |
| financials | 2 | 0% | 31% | $-549 | $-1098 | ×1.00 | watch (n=2 < 20) |
| industrials | 3 | 0% | 28% | $-392 | $-1177 | ×1.00 | watch (n=3 < 20) |
| energy | 7 | 14% | 28% | $-262 | $-1834 | ×1.00 | watch (n=7 < 20) |
| us_tech | 50 | 26% | 28% | $-164 | $-8180 | ×0.75 | AVOID (neg expectancy; wr 28% < prior 37%) |

## size

| value | n | win rate | shrunk | avg P&L | total | ×mult | call |
|---|---:|---:|---:|---:|---:|---:|---|
| 2x | 24 | 38% | 37% | $-84 | $-2028 | ×1.01 | neutral |
| 4x | 14 | 21% | 28% | $-225 | $-3156 | ×1.00 | watch (n=14 < 20) |
| 3x | 17 | 24% | 28% | $-225 | $-3826 | ×1.00 | watch (n=17 < 20) |
| 1x | 56 | 45% | 44% | $-75 | $-4226 | ×1.18 | favor |


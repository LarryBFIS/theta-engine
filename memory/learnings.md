# Engine learnings — realized edge by bucket

_Generated 2026-11-27T14:15:00.234845+00:00 · from the outcomes ledger. Buckets act on the scanner only at n ≥ 20 closes (shrunk toward the global prior). Below that they're shown but inert (×1.00)._

**Global: 112 closed · win rate 37% · realized $-13444.00**

## asset_class

| value | n | win rate | shrunk | avg P&L | total | ×mult | call |
|---|---:|---:|---:|---:|---:|---:|---|
| index_etf | 50 | 54% | 51% | $-10 | $-486 | ×1.40 | favor |
| sector_etf | 5 | 20% | 31% | $-125 | $-626 | ×1.00 | watch (n=5 < 20) |
| single_name | 57 | 23% | 25% | $-216 | $-12332 | ×0.68 | AVOID (neg expectancy; wr 25% < prior 37%) |

## structure

| value | n | win rate | shrunk | avg P&L | total | ×mult | call |
|---|---:|---:|---:|---:|---:|---:|---|
| iron_condor | 8 | 12% | 26% | $-150 | $-1203 | ×1.00 | watch (n=8 < 20) |
| short_put_vertical | 74 | 45% | 44% | $-64 | $-4703 | ×1.19 | favor |
| short_call_vertical | 30 | 23% | 27% | $-251 | $-7538 | ×0.73 | AVOID (neg expectancy; wr 27% < prior 37%) |

## cluster

| value | n | win rate | shrunk | avg P&L | total | ×mult | call |
|---|---:|---:|---:|---:|---:|---:|---|
| us_index | 43 | 60% | 56% | $+5 | $+206 | ×1.50 | favor |
| healthcare | 2 | 0% | 30% | $-96 | $-191 | ×1.00 | watch (n=2 < 20) |
| metals | 2 | 50% | 39% | $-184 | $-368 | ×1.00 | watch (n=2 < 20) |
| consumer | 2 | 0% | 30% | $-298 | $-596 | ×1.00 | watch (n=2 < 20) |
| financials | 2 | 0% | 30% | $-549 | $-1098 | ×1.00 | watch (n=2 < 20) |
| industrials | 3 | 0% | 28% | $-392 | $-1177 | ×1.00 | watch (n=3 < 20) |
| energy | 7 | 14% | 27% | $-262 | $-1834 | ×1.00 | watch (n=7 < 20) |
| us_tech | 51 | 26% | 27% | $-164 | $-8387 | ×0.75 | AVOID (neg expectancy; wr 27% < prior 37%) |

## size

| value | n | win rate | shrunk | avg P&L | total | ×mult | call |
|---|---:|---:|---:|---:|---:|---:|---|
| 2x | 24 | 38% | 37% | $-84 | $-2028 | ×1.02 | neutral |
| 4x | 14 | 21% | 28% | $-225 | $-3156 | ×1.00 | watch (n=14 < 20) |
| 3x | 17 | 24% | 28% | $-225 | $-3826 | ×1.00 | watch (n=17 < 20) |
| 1x | 57 | 44% | 43% | $-78 | $-4434 | ×1.17 | favor |


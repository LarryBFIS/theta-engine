# Engine learnings — realized edge by bucket

_Generated 2026-11-19T12:48:56.093159+00:00 · from the outcomes ledger. Buckets act on the scanner only at n ≥ 20 closes (shrunk toward the global prior). Below that they're shown but inert (×1.00)._

**Global: 97 closed · win rate 42% · realized $-9354.00**

## asset_class

| value | n | win rate | shrunk | avg P&L | total | ×mult | call |
|---|---:|---:|---:|---:|---:|---:|---|
| index_etf | 44 | 61% | 58% | $+10 | $+440 | ×1.37 | favor |
| sector_etf | 5 | 20% | 35% | $-125 | $-626 | ×1.00 | watch (n=5 < 20) |
| single_name | 48 | 27% | 30% | $-191 | $-9168 | ×0.70 | AVOID (neg expectancy; wr 30% < prior 42%) |

## structure

| value | n | win rate | shrunk | avg P&L | total | ×mult | call |
|---|---:|---:|---:|---:|---:|---:|---|
| iron_condor | 8 | 12% | 29% | $-150 | $-1203 | ×1.00 | watch (n=8 < 20) |
| short_put_vertical | 65 | 51% | 50% | $-45 | $-2931 | ×1.17 | favor |
| short_call_vertical | 24 | 29% | 33% | $-218 | $-5220 | ×0.78 | AVOID (neg expectancy; wr 33% < prior 42%) |

## cluster

| value | n | win rate | shrunk | avg P&L | total | ×mult | call |
|---|---:|---:|---:|---:|---:|---:|---|
| us_index | 37 | 70% | 64% | $+31 | $+1132 | ×1.50 | favor |
| healthcare | 2 | 0% | 35% | $-96 | $-191 | ×1.00 | watch (n=2 < 20) |
| metals | 2 | 50% | 44% | $-184 | $-368 | ×1.00 | watch (n=2 < 20) |
| consumer | 2 | 0% | 35% | $-298 | $-596 | ×1.00 | watch (n=2 < 20) |
| financials | 2 | 0% | 35% | $-549 | $-1098 | ×1.00 | watch (n=2 < 20) |
| industrials | 3 | 0% | 32% | $-392 | $-1177 | ×1.00 | watch (n=3 < 20) |
| energy | 7 | 14% | 31% | $-262 | $-1834 | ×1.00 | watch (n=7 < 20) |
| us_tech | 42 | 31% | 33% | $-124 | $-5223 | ×0.78 | AVOID (neg expectancy; wr 33% < prior 42%) |

## size

| value | n | win rate | shrunk | avg P&L | total | ×mult | call |
|---|---:|---:|---:|---:|---:|---:|---|
| 1x | 43 | 58% | 55% | $-18 | $-754 | ×1.30 | favor |
| 2x | 23 | 39% | 40% | $-70 | $-1617 | ×0.95 | AVOID (neg expectancy; wr 40% < prior 42%) |
| 4x | 14 | 21% | 30% | $-225 | $-3156 | ×1.00 | watch (n=14 < 20) |
| 3x | 17 | 24% | 30% | $-225 | $-3826 | ×1.00 | watch (n=17 < 20) |


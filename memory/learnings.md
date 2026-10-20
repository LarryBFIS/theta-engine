# Engine learnings — realized edge by bucket

_Generated 2026-10-20T17:33:16.062217+00:00 · from the outcomes ledger. Buckets act on the scanner only at n ≥ 20 closes (shrunk toward the global prior). Below that they're shown but inert (×1.00)._

**Global: 88 closed · win rate 41% · realized $-9284.50**

## asset_class

| value | n | win rate | shrunk | avg P&L | total | ×mult | call |
|---|---:|---:|---:|---:|---:|---:|---|
| index_etf | 38 | 60% | 56% | $+8 | $+314 | ×1.38 | favor |
| sector_etf | 4 | 25% | 36% | $-130 | $-518 | ×1.00 | watch (n=4 < 20) |
| single_name | 46 | 26% | 29% | $-197 | $-9080 | ×0.70 | AVOID (neg expectancy; wr 29% < prior 41%) |

## structure

| value | n | win rate | shrunk | avg P&L | total | ×mult | call |
|---|---:|---:|---:|---:|---:|---:|---|
| iron_condor | 8 | 12% | 28% | $-150 | $-1203 | ×1.00 | watch (n=8 < 20) |
| short_put_vertical | 59 | 51% | 49% | $-47 | $-2755 | ×1.21 | favor |
| short_call_vertical | 21 | 24% | 29% | $-254 | $-5326 | ×0.72 | AVOID (neg expectancy; wr 29% < prior 41%) |

## cluster

| value | n | win rate | shrunk | avg P&L | total | ×mult | call |
|---|---:|---:|---:|---:|---:|---:|---|
| us_index | 31 | 71% | 64% | $+32 | $+1006 | ×1.50 | favor |
| healthcare | 1 | 0% | 37% | $-84 | $-84 | ×1.00 | watch (n=1 < 20) |
| metals | 2 | 50% | 42% | $-184 | $-368 | ×1.00 | watch (n=2 < 20) |
| consumer | 2 | 0% | 34% | $-298 | $-596 | ×1.00 | watch (n=2 < 20) |
| financials | 2 | 0% | 34% | $-549 | $-1098 | ×1.00 | watch (n=2 < 20) |
| industrials | 3 | 0% | 32% | $-392 | $-1177 | ×1.00 | watch (n=3 < 20) |
| energy | 7 | 14% | 30% | $-262 | $-1834 | ×1.00 | watch (n=7 < 20) |
| us_tech | 40 | 30% | 32% | $-128 | $-5135 | ×0.79 | AVOID (neg expectancy; wr 32% < prior 41%) |

## size

| value | n | win rate | shrunk | avg P&L | total | ×mult | call |
|---|---:|---:|---:|---:|---:|---:|---|
| 1x | 34 | 59% | 55% | $-20 | $-685 | ×1.34 | favor |
| 2x | 23 | 39% | 40% | $-70 | $-1617 | ×0.97 | AVOID (neg expectancy; wr 40% < prior 41%) |
| 4x | 14 | 21% | 30% | $-225 | $-3156 | ×1.00 | watch (n=14 < 20) |
| 3x | 17 | 24% | 30% | $-225 | $-3826 | ×1.00 | watch (n=17 < 20) |


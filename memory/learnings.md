# Engine learnings — realized edge by bucket

_Generated 2026-11-20T20:45:12.027842+00:00 · from the outcomes ledger. Buckets act on the scanner only at n ≥ 20 closes (shrunk toward the global prior). Below that they're shown but inert (×1.00)._

**Global: 103 closed · win rate 40% · realized $-11421.00**

## asset_class

| value | n | win rate | shrunk | avg P&L | total | ×mult | call |
|---|---:|---:|---:|---:|---:|---:|---|
| index_etf | 46 | 59% | 55% | $+4 | $+173 | ×1.39 | favor |
| sector_etf | 5 | 20% | 33% | $-125 | $-626 | ×1.00 | watch (n=5 < 20) |
| single_name | 52 | 25% | 27% | $-211 | $-10968 | ×0.69 | AVOID (neg expectancy; wr 27% < prior 40%) |

## structure

| value | n | win rate | shrunk | avg P&L | total | ×mult | call |
|---|---:|---:|---:|---:|---:|---:|---|
| iron_condor | 8 | 12% | 28% | $-150 | $-1203 | ×1.00 | watch (n=8 < 20) |
| short_put_vertical | 68 | 48% | 47% | $-50 | $-3428 | ×1.19 | favor |
| short_call_vertical | 27 | 26% | 30% | $-251 | $-6790 | ×0.75 | AVOID (neg expectancy; wr 30% < prior 40%) |

## cluster

| value | n | win rate | shrunk | avg P&L | total | ×mult | call |
|---|---:|---:|---:|---:|---:|---:|---|
| us_index | 39 | 67% | 61% | $+22 | $+866 | ×1.50 | favor |
| healthcare | 2 | 0% | 33% | $-96 | $-191 | ×1.00 | watch (n=2 < 20) |
| metals | 2 | 50% | 42% | $-184 | $-368 | ×1.00 | watch (n=2 < 20) |
| consumer | 2 | 0% | 33% | $-298 | $-596 | ×1.00 | watch (n=2 < 20) |
| financials | 2 | 0% | 33% | $-549 | $-1098 | ×1.00 | watch (n=2 < 20) |
| industrials | 3 | 0% | 31% | $-392 | $-1177 | ×1.00 | watch (n=3 < 20) |
| energy | 7 | 14% | 29% | $-262 | $-1834 | ×1.00 | watch (n=7 < 20) |
| us_tech | 46 | 28% | 30% | $-153 | $-7023 | ×0.76 | AVOID (neg expectancy; wr 30% < prior 40%) |

## size

| value | n | win rate | shrunk | avg P&L | total | ×mult | call |
|---|---:|---:|---:|---:|---:|---:|---|
| 2x | 23 | 39% | 39% | $-70 | $-1617 | ×0.99 | AVOID (neg expectancy; wr 39% < prior 40%) |
| 1x | 49 | 51% | 49% | $-58 | $-2822 | ×1.23 | favor |
| 4x | 14 | 21% | 29% | $-225 | $-3156 | ×1.00 | watch (n=14 < 20) |
| 3x | 17 | 24% | 30% | $-225 | $-3826 | ×1.00 | watch (n=17 < 20) |


# Engine learnings — realized edge by bucket

_Generated 2026-11-23T15:48:57.854666+00:00 · from the outcomes ledger. Buckets act on the scanner only at n ≥ 20 closes (shrunk toward the global prior). Below that they're shown but inert (×1.00)._

**Global: 105 closed · win rate 39% · realized $-11734.00**

## asset_class

| value | n | win rate | shrunk | avg P&L | total | ×mult | call |
|---|---:|---:|---:|---:|---:|---:|---|
| index_etf | 47 | 57% | 54% | $+1 | $+64 | ×1.39 | favor |
| sector_etf | 5 | 20% | 33% | $-125 | $-626 | ×1.00 | watch (n=5 < 20) |
| single_name | 53 | 24% | 27% | $-211 | $-11172 | ×0.69 | AVOID (neg expectancy; wr 27% < prior 39%) |

## structure

| value | n | win rate | shrunk | avg P&L | total | ×mult | call |
|---|---:|---:|---:|---:|---:|---:|---|
| iron_condor | 8 | 12% | 27% | $-150 | $-1203 | ×1.00 | watch (n=8 < 20) |
| short_put_vertical | 70 | 47% | 46% | $-53 | $-3742 | ×1.18 | favor |
| short_call_vertical | 27 | 26% | 30% | $-251 | $-6790 | ×0.76 | AVOID (neg expectancy; wr 29% < prior 39%) |

## cluster

| value | n | win rate | shrunk | avg P&L | total | ×mult | call |
|---|---:|---:|---:|---:|---:|---:|---|
| us_index | 40 | 65% | 60% | $+19 | $+757 | ×1.50 | favor |
| healthcare | 2 | 0% | 32% | $-96 | $-191 | ×1.00 | watch (n=2 < 20) |
| metals | 2 | 50% | 41% | $-184 | $-368 | ×1.00 | watch (n=2 < 20) |
| consumer | 2 | 0% | 32% | $-298 | $-596 | ×1.00 | watch (n=2 < 20) |
| financials | 2 | 0% | 32% | $-549 | $-1098 | ×1.00 | watch (n=2 < 20) |
| industrials | 3 | 0% | 30% | $-392 | $-1177 | ×1.00 | watch (n=3 < 20) |
| energy | 7 | 14% | 29% | $-262 | $-1834 | ×1.00 | watch (n=7 < 20) |
| us_tech | 47 | 28% | 30% | $-154 | $-7228 | ×0.76 | AVOID (neg expectancy; wr 30% < prior 39%) |

## size

| value | n | win rate | shrunk | avg P&L | total | ×mult | call |
|---|---:|---:|---:|---:|---:|---:|---|
| 2x | 23 | 39% | 39% | $-70 | $-1617 | ×1.00 | neutral |
| 1x | 51 | 49% | 47% | $-61 | $-3134 | ×1.21 | favor |
| 4x | 14 | 21% | 29% | $-225 | $-3156 | ×1.00 | watch (n=14 < 20) |
| 3x | 17 | 24% | 29% | $-225 | $-3826 | ×1.00 | watch (n=17 < 20) |


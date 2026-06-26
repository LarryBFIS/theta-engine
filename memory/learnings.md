# Engine learnings — realized edge by bucket

_Generated 2026-06-26T13:27:40.097551+00:00 · from the outcomes ledger. Buckets act on the scanner only at n ≥ 20 closes (shrunk toward the global prior). Below that they're shown but inert (×1.00)._

**Global: 42 closed · win rate 31% · realized $-5952.00**

## asset_class

| value | n | win rate | shrunk | avg P&L | total | ×mult | call |
|---|---:|---:|---:|---:|---:|---:|---|
| index_etf | 15 | 53% | 44% | $+3 | $+46 | ×1.00 | watch (n=15 < 20) |
| sector_etf | 1 | 0% | 28% | $-418 | $-418 | ×1.00 | watch (n=1 < 20) |
| single_name | 26 | 19% | 22% | $-215 | $-5580 | ×0.73 | AVOID (neg expectancy; wr 22% < prior 31%) |

## structure

| value | n | win rate | shrunk | avg P&L | total | ×mult | call |
|---|---:|---:|---:|---:|---:|---:|---|
| iron_condor | 6 | 0% | 19% | $-197 | $-1182 | ×1.00 | watch (n=6 < 20) |
| short_call_vertical | 7 | 14% | 24% | $-338 | $-2363 | ×1.00 | watch (n=7 < 20) |
| short_put_vertical | 29 | 41% | 39% | $-83 | $-2407 | ×1.25 | favor |

## cluster

| value | n | win rate | shrunk | avg P&L | total | ×mult | call |
|---|---:|---:|---:|---:|---:|---:|---|
| us_index | 8 | 88% | 56% | $+92 | $+739 | ×1.00 | watch (n=8 < 20) |
| consumer | 1 | 0% | 28% | $-385 | $-385 | ×1.00 | watch (n=1 < 20) |
| metals | 1 | 0% | 28% | $-418 | $-418 | ×1.00 | watch (n=1 < 20) |
| industrials | 1 | 0% | 28% | $-434 | $-434 | ×1.00 | watch (n=1 < 20) |
| energy | 3 | 33% | 32% | $-308 | $-924 | ×1.00 | watch (n=3 < 20) |
| financials | 2 | 0% | 26% | $-549 | $-1098 | ×1.00 | watch (n=2 < 20) |
| us_tech | 26 | 19% | 22% | $-132 | $-3432 | ×0.73 | AVOID (neg expectancy; wr 22% < prior 31%) |

## size

| value | n | win rate | shrunk | avg P&L | total | ×mult | call |
|---|---:|---:|---:|---:|---:|---:|---|
| 1x | 2 | 50% | 34% | $-76 | $-152 | ×1.00 | watch (n=2 < 20) |
| 2x | 18 | 39% | 36% | $-62 | $-1120 | ×1.00 | watch (n=18 < 20) |
| 3x | 8 | 25% | 28% | $-190 | $-1524 | ×1.00 | watch (n=8 < 20) |
| 4x | 14 | 21% | 25% | $-225 | $-3156 | ×1.00 | watch (n=14 < 20) |


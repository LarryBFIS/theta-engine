# Engine learnings — realized edge by bucket

_Generated 2026-07-03T17:45:06.992118+00:00 · from the outcomes ledger. Buckets act on the scanner only at n ≥ 20 closes (shrunk toward the global prior). Below that they're shown but inert (×1.00)._

**Global: 55 closed · win rate 31% · realized $-8692.00**

## asset_class

| value | n | win rate | shrunk | avg P&L | total | ×mult | call |
|---|---:|---:|---:|---:|---:|---:|---|
| index_etf | 17 | 59% | 48% | $+13 | $+225 | ×1.00 | watch (n=17 < 20) |
| sector_etf | 2 | 50% | 34% | $-184 | $-368 | ×1.00 | watch (n=2 < 20) |
| single_name | 36 | 17% | 20% | $-237 | $-8548 | ×0.64 | AVOID (neg expectancy; wr 20% < prior 31%) |

## structure

| value | n | win rate | shrunk | avg P&L | total | ×mult | call |
|---|---:|---:|---:|---:|---:|---:|---|
| iron_condor | 6 | 0% | 19% | $-197 | $-1182 | ×1.00 | watch (n=6 < 20) |
| short_put_vertical | 35 | 46% | 42% | $-75 | $-2639 | ×1.37 | favor |
| short_call_vertical | 14 | 7% | 17% | $-348 | $-4871 | ×1.00 | watch (n=14 < 20) |

## cluster

| value | n | win rate | shrunk | avg P&L | total | ×mult | call |
|---|---:|---:|---:|---:|---:|---:|---|
| us_index | 10 | 90% | 60% | $+92 | $+918 | ×1.00 | watch (n=10 < 20) |
| metals | 2 | 50% | 34% | $-184 | $-368 | ×1.00 | watch (n=2 < 20) |
| consumer | 2 | 0% | 26% | $-298 | $-596 | ×1.00 | watch (n=2 < 20) |
| financials | 2 | 0% | 26% | $-549 | $-1098 | ×1.00 | watch (n=2 < 20) |
| industrials | 3 | 0% | 24% | $-392 | $-1177 | ×1.00 | watch (n=3 < 20) |
| energy | 5 | 20% | 27% | $-320 | $-1602 | ×1.00 | watch (n=5 < 20) |
| us_tech | 31 | 19% | 22% | $-154 | $-4768 | ×0.72 | AVOID (neg expectancy; wr 22% < prior 31%) |

## size

| value | n | win rate | shrunk | avg P&L | total | ×mult | call |
|---|---:|---:|---:|---:|---:|---:|---|
| 1x | 3 | 33% | 32% | $-121 | $-362 | ×1.00 | watch (n=3 < 20) |
| 2x | 21 | 43% | 39% | $-64 | $-1347 | ×1.26 | favor |
| 4x | 14 | 21% | 25% | $-225 | $-3156 | ×1.00 | watch (n=14 < 20) |
| 3x | 17 | 24% | 26% | $-225 | $-3826 | ×1.00 | watch (n=17 < 20) |


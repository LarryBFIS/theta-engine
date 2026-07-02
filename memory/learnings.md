# Engine learnings — realized edge by bucket

_Generated 2026-07-02T14:31:28.771877+00:00 · from the outcomes ledger. Buckets act on the scanner only at n ≥ 20 closes (shrunk toward the global prior). Below that they're shown but inert (×1.00)._

**Global: 54 closed · win rate 30% · realized $-8741.50**

## asset_class

| value | n | win rate | shrunk | avg P&L | total | ×mult | call |
|---|---:|---:|---:|---:|---:|---:|---|
| index_etf | 17 | 59% | 48% | $+13 | $+225 | ×1.00 | watch (n=17 < 20) |
| sector_etf | 1 | 0% | 27% | $-418 | $-418 | ×1.00 | watch (n=1 < 20) |
| single_name | 36 | 17% | 20% | $-237 | $-8548 | ×0.66 | AVOID (neg expectancy; wr 19% < prior 30%) |

## structure

| value | n | win rate | shrunk | avg P&L | total | ×mult | call |
|---|---:|---:|---:|---:|---:|---:|---|
| iron_condor | 6 | 0% | 18% | $-197 | $-1182 | ×1.00 | watch (n=6 < 20) |
| short_put_vertical | 34 | 44% | 41% | $-79 | $-2688 | ×1.38 | favor |
| short_call_vertical | 14 | 7% | 16% | $-348 | $-4871 | ×1.00 | watch (n=14 < 20) |

## cluster

| value | n | win rate | shrunk | avg P&L | total | ×mult | call |
|---|---:|---:|---:|---:|---:|---:|---|
| us_index | 10 | 90% | 60% | $+92 | $+918 | ×1.00 | watch (n=10 < 20) |
| metals | 1 | 0% | 27% | $-418 | $-418 | ×1.00 | watch (n=1 < 20) |
| consumer | 2 | 0% | 25% | $-298 | $-596 | ×1.00 | watch (n=2 < 20) |
| financials | 2 | 0% | 25% | $-549 | $-1098 | ×1.00 | watch (n=2 < 20) |
| industrials | 3 | 0% | 23% | $-392 | $-1177 | ×1.00 | watch (n=3 < 20) |
| energy | 5 | 20% | 26% | $-320 | $-1602 | ×1.00 | watch (n=5 < 20) |
| us_tech | 31 | 19% | 22% | $-154 | $-4768 | ×0.74 | AVOID (neg expectancy; wr 22% < prior 30%) |

## size

| value | n | win rate | shrunk | avg P&L | total | ×mult | call |
|---|---:|---:|---:|---:|---:|---:|---|
| 1x | 3 | 33% | 30% | $-121 | $-362 | ×1.00 | watch (n=3 < 20) |
| 2x | 21 | 43% | 39% | $-64 | $-1347 | ×1.30 | favor |
| 4x | 14 | 21% | 25% | $-225 | $-3156 | ×1.00 | watch (n=14 < 20) |
| 3x | 16 | 19% | 23% | $-242 | $-3876 | ×1.00 | watch (n=16 < 20) |


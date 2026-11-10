# Engine learnings — realized edge by bucket

_Generated 2026-11-10T20:01:33.224473+00:00 · from the outcomes ledger. Buckets act on the scanner only at n ≥ 20 closes (shrunk toward the global prior). Below that they're shown but inert (×1.00)._

**Global: 92 closed · win rate 40% · realized $-9438.50**

## asset_class

| value | n | win rate | shrunk | avg P&L | total | ×mult | call |
|---|---:|---:|---:|---:|---:|---:|---|
| index_etf | 41 | 58% | 55% | $+7 | $+300 | ×1.37 | favor |
| sector_etf | 4 | 25% | 36% | $-130 | $-518 | ×1.00 | watch (n=4 < 20) |
| single_name | 47 | 26% | 28% | $-196 | $-9220 | ×0.70 | AVOID (neg expectancy; wr 28% < prior 40%) |

## structure

| value | n | win rate | shrunk | avg P&L | total | ×mult | call |
|---|---:|---:|---:|---:|---:|---:|---|
| iron_condor | 8 | 12% | 28% | $-150 | $-1203 | ×1.00 | watch (n=8 < 20) |
| short_put_vertical | 62 | 50% | 49% | $-47 | $-2896 | ×1.21 | favor |
| short_call_vertical | 22 | 23% | 28% | $-243 | $-5340 | ×0.70 | AVOID (neg expectancy; wr 28% < prior 40%) |

## cluster

| value | n | win rate | shrunk | avg P&L | total | ×mult | call |
|---|---:|---:|---:|---:|---:|---:|---|
| us_index | 34 | 68% | 61% | $+29 | $+992 | ×1.50 | favor |
| healthcare | 1 | 0% | 37% | $-84 | $-84 | ×1.00 | watch (n=1 < 20) |
| metals | 2 | 50% | 42% | $-184 | $-368 | ×1.00 | watch (n=2 < 20) |
| consumer | 2 | 0% | 34% | $-298 | $-596 | ×1.00 | watch (n=2 < 20) |
| financials | 2 | 0% | 34% | $-549 | $-1098 | ×1.00 | watch (n=2 < 20) |
| industrials | 3 | 0% | 31% | $-392 | $-1177 | ×1.00 | watch (n=3 < 20) |
| energy | 7 | 14% | 30% | $-262 | $-1834 | ×1.00 | watch (n=7 < 20) |
| us_tech | 41 | 29% | 31% | $-129 | $-5274 | ×0.78 | AVOID (neg expectancy; wr 31% < prior 40%) |

## size

| value | n | win rate | shrunk | avg P&L | total | ×mult | call |
|---|---:|---:|---:|---:|---:|---:|---|
| 1x | 38 | 55% | 52% | $-22 | $-839 | ×1.30 | favor |
| 2x | 23 | 39% | 40% | $-70 | $-1617 | ×0.98 | AVOID (neg expectancy; wr 39% < prior 40%) |
| 4x | 14 | 21% | 29% | $-225 | $-3156 | ×1.00 | watch (n=14 < 20) |
| 3x | 17 | 24% | 30% | $-225 | $-3826 | ×1.00 | watch (n=17 < 20) |


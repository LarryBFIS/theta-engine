# Engine learnings — realized edge by bucket

_Generated 2026-10-05T20:48:26.747472+00:00 · from the outcomes ledger. Buckets act on the scanner only at n ≥ 20 closes (shrunk toward the global prior). Below that they're shown but inert (×1.00)._

**Global: 82 closed · win rate 40% · realized $-9251.00**

## asset_class

| value | n | win rate | shrunk | avg P&L | total | ×mult | call |
|---|---:|---:|---:|---:|---:|---:|---|
| index_etf | 33 | 61% | 56% | $+8 | $+280 | ×1.39 | favor |
| sector_etf | 4 | 25% | 36% | $-130 | $-518 | ×1.00 | watch (n=4 < 20) |
| single_name | 45 | 27% | 29% | $-200 | $-9013 | ×0.72 | AVOID (neg expectancy; wr 29% < prior 40%) |

## structure

| value | n | win rate | shrunk | avg P&L | total | ×mult | call |
|---|---:|---:|---:|---:|---:|---:|---|
| iron_condor | 7 | 14% | 30% | $-162 | $-1136 | ×1.00 | watch (n=7 < 20) |
| short_put_vertical | 58 | 50% | 49% | $-48 | $-2810 | ×1.21 | favor |
| short_call_vertical | 17 | 18% | 26% | $-312 | $-5304 | ×1.00 | watch (n=17 < 20) |

## cluster

| value | n | win rate | shrunk | avg P&L | total | ×mult | call |
|---|---:|---:|---:|---:|---:|---:|---|
| us_index | 26 | 73% | 64% | $+37 | $+973 | ×1.50 | favor |
| healthcare | 1 | 0% | 37% | $-84 | $-84 | ×1.00 | watch (n=1 < 20) |
| metals | 2 | 50% | 42% | $-184 | $-368 | ×1.00 | watch (n=2 < 20) |
| consumer | 2 | 0% | 34% | $-298 | $-596 | ×1.00 | watch (n=2 < 20) |
| financials | 2 | 0% | 34% | $-549 | $-1098 | ×1.00 | watch (n=2 < 20) |
| industrials | 3 | 0% | 31% | $-392 | $-1177 | ×1.00 | watch (n=3 < 20) |
| energy | 7 | 14% | 30% | $-262 | $-1834 | ×1.00 | watch (n=7 < 20) |
| us_tech | 39 | 31% | 33% | $-130 | $-5068 | ×0.81 | AVOID (neg expectancy; wr 33% < prior 40%) |

## size

| value | n | win rate | shrunk | avg P&L | total | ×mult | call |
|---|---:|---:|---:|---:|---:|---:|---|
| 1x | 28 | 61% | 55% | $-23 | $-652 | ×1.38 | favor |
| 2x | 23 | 39% | 40% | $-70 | $-1617 | ×0.98 | AVOID (neg expectancy; wr 39% < prior 40%) |
| 4x | 14 | 21% | 29% | $-225 | $-3156 | ×1.00 | watch (n=14 < 20) |
| 3x | 17 | 24% | 30% | $-225 | $-3826 | ×1.00 | watch (n=17 < 20) |


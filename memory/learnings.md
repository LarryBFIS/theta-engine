# Engine learnings — realized edge by bucket

_Generated 2026-10-09T18:46:18.814982+00:00 · from the outcomes ledger. Buckets act on the scanner only at n ≥ 20 closes (shrunk toward the global prior). Below that they're shown but inert (×1.00)._

**Global: 85 closed · win rate 41% · realized $-9170.50**

## asset_class

| value | n | win rate | shrunk | avg P&L | total | ×mult | call |
|---|---:|---:|---:|---:|---:|---:|---|
| index_etf | 36 | 61% | 57% | $+10 | $+361 | ×1.38 | favor |
| sector_etf | 4 | 25% | 37% | $-130 | $-518 | ×1.00 | watch (n=4 < 20) |
| single_name | 45 | 27% | 29% | $-200 | $-9013 | ×0.71 | AVOID (neg expectancy; wr 29% < prior 41%) |

## structure

| value | n | win rate | shrunk | avg P&L | total | ×mult | call |
|---|---:|---:|---:|---:|---:|---:|---|
| iron_condor | 7 | 14% | 30% | $-162 | $-1136 | ×1.00 | watch (n=7 < 20) |
| short_put_vertical | 59 | 51% | 49% | $-47 | $-2755 | ×1.20 | favor |
| short_call_vertical | 19 | 21% | 28% | $-278 | $-5280 | ×1.00 | watch (n=19 < 20) |

## cluster

| value | n | win rate | shrunk | avg P&L | total | ×mult | call |
|---|---:|---:|---:|---:|---:|---:|---|
| us_index | 29 | 72% | 64% | $+36 | $+1054 | ×1.50 | favor |
| healthcare | 1 | 0% | 37% | $-84 | $-84 | ×1.00 | watch (n=1 < 20) |
| metals | 2 | 50% | 43% | $-184 | $-368 | ×1.00 | watch (n=2 < 20) |
| consumer | 2 | 0% | 34% | $-298 | $-596 | ×1.00 | watch (n=2 < 20) |
| financials | 2 | 0% | 34% | $-549 | $-1098 | ×1.00 | watch (n=2 < 20) |
| industrials | 3 | 0% | 32% | $-392 | $-1177 | ×1.00 | watch (n=3 < 20) |
| energy | 7 | 14% | 30% | $-262 | $-1834 | ×1.00 | watch (n=7 < 20) |
| us_tech | 39 | 31% | 33% | $-130 | $-5068 | ×0.80 | AVOID (neg expectancy; wr 33% < prior 41%) |

## size

| value | n | win rate | shrunk | avg P&L | total | ×mult | call |
|---|---:|---:|---:|---:|---:|---:|---|
| 1x | 31 | 61% | 56% | $-18 | $-571 | ×1.37 | favor |
| 2x | 23 | 39% | 40% | $-70 | $-1617 | ×0.96 | AVOID (neg expectancy; wr 40% < prior 41%) |
| 4x | 14 | 21% | 30% | $-225 | $-3156 | ×1.00 | watch (n=14 < 20) |
| 3x | 17 | 24% | 30% | $-225 | $-3826 | ×1.00 | watch (n=17 < 20) |


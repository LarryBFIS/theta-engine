# Engine learnings — realized edge by bucket

_Generated 2026-08-03T17:47:16.175337+00:00 · from the outcomes ledger. Buckets act on the scanner only at n ≥ 20 closes (shrunk toward the global prior). Below that they're shown but inert (×1.00)._

**Global: 61 closed · win rate 31% · realized $-9381.00**

## asset_class

| value | n | win rate | shrunk | avg P&L | total | ×mult | call |
|---|---:|---:|---:|---:|---:|---:|---|
| index_etf | 20 | 55% | 47% | $+8 | $+164 | ×1.50 | favor |
| sector_etf | 2 | 50% | 34% | $-184 | $-368 | ×1.00 | watch (n=2 < 20) |
| single_name | 39 | 18% | 21% | $-235 | $-9176 | ×0.66 | AVOID (neg expectancy; wr 21% < prior 31%) |

## structure

| value | n | win rate | shrunk | avg P&L | total | ×mult | call |
|---|---:|---:|---:|---:|---:|---:|---|
| iron_condor | 6 | 0% | 20% | $-197 | $-1182 | ×1.00 | watch (n=6 < 20) |
| short_put_vertical | 39 | 44% | 41% | $-73 | $-2865 | ×1.32 | favor |
| short_call_vertical | 16 | 12% | 20% | $-333 | $-5334 | ×1.00 | watch (n=16 < 20) |

## cluster

| value | n | win rate | shrunk | avg P&L | total | ×mult | call |
|---|---:|---:|---:|---:|---:|---:|---|
| us_index | 13 | 77% | 57% | $+66 | $+856 | ×1.00 | watch (n=13 < 20) |
| metals | 2 | 50% | 34% | $-184 | $-368 | ×1.00 | watch (n=2 < 20) |
| consumer | 2 | 0% | 26% | $-298 | $-596 | ×1.00 | watch (n=2 < 20) |
| financials | 2 | 0% | 26% | $-549 | $-1098 | ×1.00 | watch (n=2 < 20) |
| industrials | 3 | 0% | 24% | $-392 | $-1177 | ×1.00 | watch (n=3 < 20) |
| energy | 6 | 17% | 26% | $-295 | $-1768 | ×1.00 | watch (n=6 < 20) |
| us_tech | 33 | 21% | 24% | $-159 | $-5232 | ×0.76 | AVOID (neg expectancy; wr 24% < prior 31%) |

## size

| value | n | win rate | shrunk | avg P&L | total | ×mult | call |
|---|---:|---:|---:|---:|---:|---:|---|
| 1x | 7 | 43% | 36% | $-112 | $-782 | ×1.00 | watch (n=7 < 20) |
| 2x | 23 | 39% | 37% | $-70 | $-1617 | ×1.18 | favor |
| 4x | 14 | 21% | 26% | $-225 | $-3156 | ×1.00 | watch (n=14 < 20) |
| 3x | 17 | 24% | 26% | $-225 | $-3826 | ×1.00 | watch (n=17 < 20) |


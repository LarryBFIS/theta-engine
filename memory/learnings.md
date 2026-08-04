# Engine learnings — realized edge by bucket

_Generated 2026-08-04T18:19:22.807147+00:00 · from the outcomes ledger. Buckets act on the scanner only at n ≥ 20 closes (shrunk toward the global prior). Below that they're shown but inert (×1.00)._

**Global: 63 closed · win rate 33% · realized $-9294.00**

## asset_class

| value | n | win rate | shrunk | avg P&L | total | ×mult | call |
|---|---:|---:|---:|---:|---:|---:|---|
| index_etf | 21 | 57% | 50% | $+9 | $+194 | ×1.48 | favor |
| sector_etf | 2 | 50% | 36% | $-184 | $-368 | ×1.00 | watch (n=2 < 20) |
| single_name | 40 | 20% | 23% | $-228 | $-9119 | ×0.68 | AVOID (neg expectancy; wr 23% < prior 33%) |

## structure

| value | n | win rate | shrunk | avg P&L | total | ×mult | call |
|---|---:|---:|---:|---:|---:|---:|---|
| iron_condor | 6 | 0% | 21% | $-197 | $-1182 | ×1.00 | watch (n=6 < 20) |
| short_put_vertical | 41 | 46% | 44% | $-68 | $-2778 | ×1.31 | favor |
| short_call_vertical | 16 | 12% | 20% | $-333 | $-5334 | ×1.00 | watch (n=16 < 20) |

## cluster

| value | n | win rate | shrunk | avg P&L | total | ×mult | call |
|---|---:|---:|---:|---:|---:|---:|---|
| us_index | 14 | 79% | 60% | $+63 | $+886 | ×1.00 | watch (n=14 < 20) |
| metals | 2 | 50% | 36% | $-184 | $-368 | ×1.00 | watch (n=2 < 20) |
| consumer | 2 | 0% | 28% | $-298 | $-596 | ×1.00 | watch (n=2 < 20) |
| financials | 2 | 0% | 28% | $-549 | $-1098 | ×1.00 | watch (n=2 < 20) |
| industrials | 3 | 0% | 26% | $-392 | $-1177 | ×1.00 | watch (n=3 < 20) |
| energy | 6 | 17% | 27% | $-295 | $-1768 | ×1.00 | watch (n=6 < 20) |
| us_tech | 34 | 24% | 26% | $-152 | $-5174 | ×0.77 | AVOID (neg expectancy; wr 26% < prior 33%) |

## size

| value | n | win rate | shrunk | avg P&L | total | ×mult | call |
|---|---:|---:|---:|---:|---:|---:|---|
| 1x | 9 | 56% | 44% | $-77 | $-694 | ×1.00 | watch (n=9 < 20) |
| 2x | 23 | 39% | 37% | $-70 | $-1617 | ×1.12 | favor |
| 4x | 14 | 21% | 26% | $-225 | $-3156 | ×1.00 | watch (n=14 < 20) |
| 3x | 17 | 24% | 27% | $-225 | $-3826 | ×1.00 | watch (n=17 < 20) |


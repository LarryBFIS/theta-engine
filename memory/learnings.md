# Engine learnings — realized edge by bucket

_Generated 2026-08-03T20:17:53.163317+00:00 · from the outcomes ledger. Buckets act on the scanner only at n ≥ 20 closes (shrunk toward the global prior). Below that they're shown but inert (×1.00)._

**Global: 62 closed · win rate 32% · realized $-9351.50**

## asset_class

| value | n | win rate | shrunk | avg P&L | total | ×mult | call |
|---|---:|---:|---:|---:|---:|---:|---|
| index_etf | 21 | 57% | 49% | $+9 | $+194 | ×1.50 | favor |
| sector_etf | 2 | 50% | 35% | $-184 | $-368 | ×1.00 | watch (n=2 < 20) |
| single_name | 39 | 18% | 21% | $-235 | $-9176 | ×0.65 | AVOID (neg expectancy; wr 21% < prior 32%) |

## structure

| value | n | win rate | shrunk | avg P&L | total | ×mult | call |
|---|---:|---:|---:|---:|---:|---:|---|
| iron_condor | 6 | 0% | 20% | $-197 | $-1182 | ×1.00 | watch (n=6 < 20) |
| short_put_vertical | 40 | 45% | 42% | $-71 | $-2836 | ×1.32 | favor |
| short_call_vertical | 16 | 12% | 20% | $-333 | $-5334 | ×1.00 | watch (n=16 < 20) |

## cluster

| value | n | win rate | shrunk | avg P&L | total | ×mult | call |
|---|---:|---:|---:|---:|---:|---:|---|
| us_index | 14 | 79% | 59% | $+63 | $+886 | ×1.00 | watch (n=14 < 20) |
| metals | 2 | 50% | 35% | $-184 | $-368 | ×1.00 | watch (n=2 < 20) |
| consumer | 2 | 0% | 27% | $-298 | $-596 | ×1.00 | watch (n=2 < 20) |
| financials | 2 | 0% | 27% | $-549 | $-1098 | ×1.00 | watch (n=2 < 20) |
| industrials | 3 | 0% | 25% | $-392 | $-1177 | ×1.00 | watch (n=3 < 20) |
| energy | 6 | 17% | 26% | $-295 | $-1768 | ×1.00 | watch (n=6 < 20) |
| us_tech | 33 | 21% | 24% | $-159 | $-5232 | ×0.74 | AVOID (neg expectancy; wr 24% < prior 32%) |

## size

| value | n | win rate | shrunk | avg P&L | total | ×mult | call |
|---|---:|---:|---:|---:|---:|---:|---|
| 1x | 8 | 50% | 40% | $-94 | $-752 | ×1.00 | watch (n=8 < 20) |
| 2x | 23 | 39% | 37% | $-70 | $-1617 | ×1.15 | favor |
| 4x | 14 | 21% | 26% | $-225 | $-3156 | ×1.00 | watch (n=14 < 20) |
| 3x | 17 | 24% | 27% | $-225 | $-3826 | ×1.00 | watch (n=17 < 20) |


# Engine learnings — realized edge by bucket

_Generated 2026-07-31T14:31:15.401296+00:00 · from the outcomes ledger. Buckets act on the scanner only at n ≥ 20 closes (shrunk toward the global prior). Below that they're shown but inert (×1.00)._

**Global: 60 closed · win rate 30% · realized $-9432.50**

## asset_class

| value | n | win rate | shrunk | avg P&L | total | ×mult | call |
|---|---:|---:|---:|---:|---:|---:|---|
| index_etf | 19 | 53% | 45% | $+6 | $+112 | ×1.00 | watch (n=19 < 20) |
| sector_etf | 2 | 50% | 33% | $-184 | $-368 | ×1.00 | watch (n=2 < 20) |
| single_name | 39 | 18% | 20% | $-235 | $-9176 | ×0.68 | AVOID (neg expectancy; wr 20% < prior 30%) |

## structure

| value | n | win rate | shrunk | avg P&L | total | ×mult | call |
|---|---:|---:|---:|---:|---:|---:|---|
| iron_condor | 6 | 0% | 19% | $-197 | $-1182 | ×1.00 | watch (n=6 < 20) |
| short_put_vertical | 38 | 42% | 40% | $-77 | $-2916 | ×1.32 | favor |
| short_call_vertical | 16 | 12% | 19% | $-333 | $-5334 | ×1.00 | watch (n=16 < 20) |

## cluster

| value | n | win rate | shrunk | avg P&L | total | ×mult | call |
|---|---:|---:|---:|---:|---:|---:|---|
| us_index | 12 | 75% | 55% | $+67 | $+805 | ×1.00 | watch (n=12 < 20) |
| metals | 2 | 50% | 33% | $-184 | $-368 | ×1.00 | watch (n=2 < 20) |
| consumer | 2 | 0% | 25% | $-298 | $-596 | ×1.00 | watch (n=2 < 20) |
| financials | 2 | 0% | 25% | $-549 | $-1098 | ×1.00 | watch (n=2 < 20) |
| industrials | 3 | 0% | 23% | $-392 | $-1177 | ×1.00 | watch (n=3 < 20) |
| energy | 6 | 17% | 25% | $-295 | $-1768 | ×1.00 | watch (n=6 < 20) |
| us_tech | 33 | 21% | 23% | $-159 | $-5232 | ×0.78 | AVOID (neg expectancy; wr 23% < prior 30%) |

## size

| value | n | win rate | shrunk | avg P&L | total | ×mult | call |
|---|---:|---:|---:|---:|---:|---:|---|
| 1x | 6 | 33% | 31% | $-139 | $-833 | ×1.00 | watch (n=6 < 20) |
| 2x | 23 | 39% | 36% | $-70 | $-1617 | ×1.21 | favor |
| 4x | 14 | 21% | 25% | $-225 | $-3156 | ×1.00 | watch (n=14 < 20) |
| 3x | 17 | 24% | 26% | $-225 | $-3826 | ×1.00 | watch (n=17 < 20) |


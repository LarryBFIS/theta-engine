# Engine learnings — realized edge by bucket

_Generated 2026-08-13T14:10:22.138772+00:00 · from the outcomes ledger. Buckets act on the scanner only at n ≥ 20 closes (shrunk toward the global prior). Below that they're shown but inert (×1.00)._

**Global: 66 closed · win rate 36% · realized $-9169.50**

## asset_class

| value | n | win rate | shrunk | avg P&L | total | ×mult | call |
|---|---:|---:|---:|---:|---:|---:|---|
| index_etf | 23 | 61% | 53% | $+11 | $+262 | ×1.47 | favor |
| sector_etf | 2 | 50% | 39% | $-184 | $-368 | ×1.00 | watch (n=2 < 20) |
| single_name | 41 | 22% | 25% | $-221 | $-9064 | ×0.68 | AVOID (neg expectancy; wr 25% < prior 36%) |

## structure

| value | n | win rate | shrunk | avg P&L | total | ×mult | call |
|---|---:|---:|---:|---:|---:|---:|---|
| iron_condor | 6 | 0% | 23% | $-197 | $-1182 | ×1.00 | watch (n=6 < 20) |
| short_put_vertical | 44 | 50% | 48% | $-60 | $-2654 | ×1.31 | favor |
| short_call_vertical | 16 | 12% | 22% | $-333 | $-5334 | ×1.00 | watch (n=16 < 20) |

## cluster

| value | n | win rate | shrunk | avg P&L | total | ×mult | call |
|---|---:|---:|---:|---:|---:|---:|---|
| us_index | 16 | 81% | 64% | $+60 | $+955 | ×1.00 | watch (n=16 < 20) |
| metals | 2 | 50% | 39% | $-184 | $-368 | ×1.00 | watch (n=2 < 20) |
| consumer | 2 | 0% | 30% | $-298 | $-596 | ×1.00 | watch (n=2 < 20) |
| financials | 2 | 0% | 30% | $-549 | $-1098 | ×1.00 | watch (n=2 < 20) |
| industrials | 3 | 0% | 28% | $-392 | $-1177 | ×1.00 | watch (n=3 < 20) |
| energy | 6 | 17% | 29% | $-295 | $-1768 | ×1.00 | watch (n=6 < 20) |
| us_tech | 35 | 26% | 28% | $-146 | $-5118 | ×0.77 | AVOID (neg expectancy; wr 28% < prior 36%) |

## size

| value | n | win rate | shrunk | avg P&L | total | ×mult | call |
|---|---:|---:|---:|---:|---:|---:|---|
| 1x | 12 | 67% | 53% | $-48 | $-570 | ×1.00 | watch (n=12 < 20) |
| 2x | 23 | 39% | 38% | $-70 | $-1617 | ×1.05 | favor |
| 4x | 14 | 21% | 28% | $-225 | $-3156 | ×1.00 | watch (n=14 < 20) |
| 3x | 17 | 24% | 28% | $-225 | $-3826 | ×1.00 | watch (n=17 < 20) |


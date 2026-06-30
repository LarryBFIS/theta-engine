# Engine learnings — realized edge by bucket

_Generated 2026-06-30T17:04:10.931533+00:00 · from the outcomes ledger. Buckets act on the scanner only at n ≥ 20 closes (shrunk toward the global prior). Below that they're shown but inert (×1.00)._

**Global: 48 closed · win rate 29% · realized $-7570.50**

## asset_class

| value | n | win rate | shrunk | avg P&L | total | ×mult | call |
|---|---:|---:|---:|---:|---:|---:|---|
| index_etf | 16 | 56% | 46% | $+9 | $+140 | ×1.00 | watch (n=16 < 20) |
| sector_etf | 1 | 0% | 26% | $-418 | $-418 | ×1.00 | watch (n=1 < 20) |
| single_name | 31 | 16% | 19% | $-235 | $-7292 | ×0.66 | AVOID (neg expectancy; wr 19% < prior 29%) |

## structure

| value | n | win rate | shrunk | avg P&L | total | ×mult | call |
|---|---:|---:|---:|---:|---:|---:|---|
| iron_condor | 6 | 0% | 18% | $-197 | $-1182 | ×1.00 | watch (n=6 < 20) |
| short_put_vertical | 31 | 42% | 39% | $-84 | $-2606 | ×1.33 | favor |
| short_call_vertical | 11 | 9% | 19% | $-344 | $-3782 | ×1.00 | watch (n=11 < 20) |

## cluster

| value | n | win rate | shrunk | avg P&L | total | ×mult | call |
|---|---:|---:|---:|---:|---:|---:|---|
| us_index | 9 | 89% | 57% | $+92 | $+832 | ×1.00 | watch (n=9 < 20) |
| consumer | 1 | 0% | 26% | $-385 | $-385 | ×1.00 | watch (n=1 < 20) |
| metals | 1 | 0% | 26% | $-418 | $-418 | ×1.00 | watch (n=1 < 20) |
| industrials | 2 | 0% | 24% | $-366 | $-732 | ×1.00 | watch (n=2 < 20) |
| financials | 2 | 0% | 24% | $-549 | $-1098 | ×1.00 | watch (n=2 < 20) |
| energy | 4 | 25% | 28% | $-292 | $-1169 | ×1.00 | watch (n=4 < 20) |
| us_tech | 29 | 17% | 20% | $-159 | $-4601 | ×0.70 | AVOID (neg expectancy; wr 20% < prior 29%) |

## size

| value | n | win rate | shrunk | avg P&L | total | ×mult | call |
|---|---:|---:|---:|---:|---:|---:|---|
| 1x | 2 | 50% | 33% | $-76 | $-152 | ×1.00 | watch (n=2 < 20) |
| 2x | 19 | 42% | 38% | $-54 | $-1027 | ×1.00 | watch (n=19 < 20) |
| 4x | 14 | 21% | 25% | $-225 | $-3156 | ×1.00 | watch (n=14 < 20) |
| 3x | 13 | 15% | 21% | $-249 | $-3236 | ×1.00 | watch (n=13 < 20) |


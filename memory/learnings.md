# Engine learnings — realized edge by bucket

_Generated 2026-06-24T20:22:07.856287+00:00 · from the outcomes ledger. Buckets act on the scanner only at n ≥ 20 closes (shrunk toward the global prior). Below that they're shown but inert (×1.00)._

**Global: 36 closed · win rate 33% · realized $-4459.50**

## asset_class

| value | n | win rate | shrunk | avg P&L | total | ×mult | call |
|---|---:|---:|---:|---:|---:|---:|---|
| index_etf | 14 | 57% | 47% | $+5 | $+76 | ×1.00 | watch (n=14 < 20) |
| sector_etf | 1 | 0% | 30% | $-418 | $-418 | ×1.00 | watch (n=1 < 20) |
| single_name | 21 | 19% | 24% | $-196 | $-4117 | ×0.71 | AVOID (neg expectancy; wr 24% < prior 33%) |

## structure

| value | n | win rate | shrunk | avg P&L | total | ×mult | call |
|---|---:|---:|---:|---:|---:|---:|---|
| iron_condor | 6 | 0% | 21% | $-197 | $-1182 | ×1.00 | watch (n=6 < 20) |
| short_put_vertical | 24 | 46% | 42% | $-56 | $-1348 | ×1.26 | favor |
| short_call_vertical | 6 | 17% | 27% | $-322 | $-1930 | ×1.00 | watch (n=6 < 20) |

## cluster

| value | n | win rate | shrunk | avg P&L | total | ×mult | call |
|---|---:|---:|---:|---:|---:|---:|---|
| us_index | 7 | 100% | 61% | $+110 | $+768 | ×1.00 | watch (n=7 < 20) |
| consumer | 1 | 0% | 30% | $-385 | $-385 | ×1.00 | watch (n=1 < 20) |
| metals | 1 | 0% | 30% | $-418 | $-418 | ×1.00 | watch (n=1 < 20) |
| energy | 2 | 50% | 36% | $-247 | $-494 | ×1.00 | watch (n=2 < 20) |
| financials | 1 | 0% | 30% | $-850 | $-850 | ×1.00 | watch (n=1 < 20) |
| us_tech | 24 | 17% | 22% | $-128 | $-3080 | ×0.65 | AVOID (neg expectancy; wr 22% < prior 33%) |

## size

| value | n | win rate | shrunk | avg P&L | total | ×mult | call |
|---|---:|---:|---:|---:|---:|---:|---|
| 1x | 2 | 50% | 36% | $-76 | $-152 | ×1.00 | watch (n=2 < 20) |
| 3x | 5 | 40% | 36% | $-95 | $-476 | ×1.00 | watch (n=5 < 20) |
| 2x | 16 | 38% | 36% | $-69 | $-1106 | ×1.00 | watch (n=16 < 20) |
| 4x | 13 | 23% | 28% | $-210 | $-2726 | ×1.00 | watch (n=13 < 20) |


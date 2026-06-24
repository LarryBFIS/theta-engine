# Engine learnings — realized edge by bucket

_Generated 2026-06-24T18:21:44.095620+00:00 · from the outcomes ledger. Buckets act on the scanner only at n ≥ 20 closes (shrunk toward the global prior). Below that they're shown but inert (×1.00)._

**Global: 35 closed · win rate 34% · realized $-4204.50**

## asset_class

| value | n | win rate | shrunk | avg P&L | total | ×mult | call |
|---|---:|---:|---:|---:|---:|---:|---|
| index_etf | 14 | 57% | 48% | $+5 | $+76 | ×1.00 | watch (n=14 < 20) |
| sector_etf | 1 | 0% | 31% | $-418 | $-418 | ×1.00 | watch (n=1 < 20) |
| single_name | 20 | 20% | 25% | $-193 | $-3862 | ×0.72 | AVOID (neg expectancy; wr 25% < prior 34%) |

## structure

| value | n | win rate | shrunk | avg P&L | total | ×mult | call |
|---|---:|---:|---:|---:|---:|---:|---|
| short_put_vertical | 23 | 48% | 44% | $-48 | $-1093 | ×1.27 | favor |
| iron_condor | 6 | 0% | 21% | $-197 | $-1182 | ×1.00 | watch (n=6 < 20) |
| short_call_vertical | 6 | 17% | 28% | $-322 | $-1930 | ×1.00 | watch (n=6 < 20) |

## cluster

| value | n | win rate | shrunk | avg P&L | total | ×mult | call |
|---|---:|---:|---:|---:|---:|---:|---|
| us_index | 7 | 100% | 61% | $+110 | $+768 | ×1.00 | watch (n=7 < 20) |
| consumer | 1 | 0% | 31% | $-385 | $-385 | ×1.00 | watch (n=1 < 20) |
| metals | 1 | 0% | 31% | $-418 | $-418 | ×1.00 | watch (n=1 < 20) |
| energy | 2 | 50% | 37% | $-247 | $-494 | ×1.00 | watch (n=2 < 20) |
| financials | 1 | 0% | 31% | $-850 | $-850 | ×1.00 | watch (n=1 < 20) |
| us_tech | 23 | 17% | 22% | $-123 | $-2825 | ×0.66 | AVOID (neg expectancy; wr 23% < prior 34%) |

## size

| value | n | win rate | shrunk | avg P&L | total | ×mult | call |
|---|---:|---:|---:|---:|---:|---:|---|
| 1x | 2 | 50% | 37% | $-76 | $-152 | ×1.00 | watch (n=2 < 20) |
| 3x | 5 | 40% | 36% | $-95 | $-476 | ×1.00 | watch (n=5 < 20) |
| 2x | 15 | 40% | 38% | $-57 | $-851 | ×1.00 | watch (n=15 < 20) |
| 4x | 13 | 23% | 28% | $-210 | $-2726 | ×1.00 | watch (n=13 < 20) |


# Engine learnings — realized edge by bucket

_Generated 2026-06-22T19:55:24.979947+00:00 · from the outcomes ledger. Buckets act on the scanner only at n ≥ 20 closes (shrunk toward the global prior). Below that they're shown but inert (×1.00)._

**Global: 32 closed · win rate 31% · realized $-4178.50**

## asset_class

| value | n | win rate | shrunk | avg P&L | total | ×mult | call |
|---|---:|---:|---:|---:|---:|---:|---|
| index_etf | 12 | 58% | 46% | $+12 | $+145 | ×1.00 | watch (n=12 < 20) |
| sector_etf | 1 | 0% | 28% | $-418 | $-418 | ×1.00 | watch (n=1 < 20) |
| single_name | 19 | 16% | 21% | $-206 | $-3906 | ×1.00 | watch (n=19 < 20) |

## structure

| value | n | win rate | shrunk | avg P&L | total | ×mult | call |
|---|---:|---:|---:|---:|---:|---:|---|
| short_put_vertical | 21 | 48% | 42% | $-49 | $-1024 | ×1.35 | favor |
| iron_condor | 6 | 0% | 20% | $-197 | $-1182 | ×1.00 | watch (n=6 < 20) |
| short_call_vertical | 5 | 0% | 21% | $-395 | $-1973 | ×1.00 | watch (n=5 < 20) |

## cluster

| value | n | win rate | shrunk | avg P&L | total | ×mult | call |
|---|---:|---:|---:|---:|---:|---:|---|
| us_index | 6 | 100% | 57% | $+107 | $+642 | ×1.00 | watch (n=6 < 20) |
| consumer | 1 | 0% | 28% | $-385 | $-385 | ×1.00 | watch (n=1 < 20) |
| metals | 1 | 0% | 28% | $-418 | $-418 | ×1.00 | watch (n=1 < 20) |
| energy | 1 | 0% | 28% | $-538 | $-538 | ×1.00 | watch (n=1 < 20) |
| financials | 1 | 0% | 28% | $-850 | $-850 | ×1.00 | watch (n=1 < 20) |
| us_tech | 22 | 18% | 22% | $-120 | $-2630 | ×0.71 | AVOID (neg expectancy; wr 22% < prior 31%) |

## size

| value | n | win rate | shrunk | avg P&L | total | ×mult | call |
|---|---:|---:|---:|---:|---:|---:|---|
| 3x | 5 | 40% | 34% | $-95 | $-476 | ×1.00 | watch (n=5 < 20) |
| 2x | 15 | 40% | 36% | $-57 | $-851 | ×1.00 | watch (n=15 < 20) |
| 4x | 12 | 17% | 23% | $-238 | $-2852 | ×1.00 | watch (n=12 < 20) |


# Engine learnings — realized edge by bucket

_Generated 2026-06-23T15:50:21.078765+00:00 · from the outcomes ledger. Buckets act on the scanner only at n ≥ 20 closes (shrunk toward the global prior). Below that they're shown but inert (×1.00)._

**Global: 33 closed · win rate 30% · realized $-4374.00**

## asset_class

| value | n | win rate | shrunk | avg P&L | total | ×mult | call |
|---|---:|---:|---:|---:|---:|---:|---|
| index_etf | 13 | 54% | 44% | $-4 | $-50 | ×1.00 | watch (n=13 < 20) |
| sector_etf | 1 | 0% | 28% | $-418 | $-418 | ×1.00 | watch (n=1 < 20) |
| single_name | 19 | 16% | 21% | $-206 | $-3906 | ×1.00 | watch (n=19 < 20) |

## structure

| value | n | win rate | shrunk | avg P&L | total | ×mult | call |
|---|---:|---:|---:|---:|---:|---:|---|
| iron_condor | 6 | 0% | 19% | $-197 | $-1182 | ×1.00 | watch (n=6 < 20) |
| short_put_vertical | 22 | 46% | 41% | $-55 | $-1219 | ×1.34 | favor |
| short_call_vertical | 5 | 0% | 20% | $-395 | $-1973 | ×1.00 | watch (n=5 < 20) |

## cluster

| value | n | win rate | shrunk | avg P&L | total | ×mult | call |
|---|---:|---:|---:|---:|---:|---:|---|
| us_index | 6 | 100% | 56% | $+107 | $+642 | ×1.00 | watch (n=6 < 20) |
| consumer | 1 | 0% | 28% | $-385 | $-385 | ×1.00 | watch (n=1 < 20) |
| metals | 1 | 0% | 28% | $-418 | $-418 | ×1.00 | watch (n=1 < 20) |
| energy | 1 | 0% | 28% | $-538 | $-538 | ×1.00 | watch (n=1 < 20) |
| financials | 1 | 0% | 28% | $-850 | $-850 | ×1.00 | watch (n=1 < 20) |
| us_tech | 23 | 17% | 21% | $-123 | $-2825 | ×0.70 | AVOID (neg expectancy; wr 21% < prior 30%) |

## size

| value | n | win rate | shrunk | avg P&L | total | ×mult | call |
|---|---:|---:|---:|---:|---:|---:|---|
| 1x | 1 | 0% | 28% | $-196 | $-196 | ×1.00 | watch (n=1 < 20) |
| 3x | 5 | 40% | 34% | $-95 | $-476 | ×1.00 | watch (n=5 < 20) |
| 2x | 15 | 40% | 36% | $-57 | $-851 | ×1.00 | watch (n=15 < 20) |
| 4x | 12 | 17% | 23% | $-238 | $-2852 | ×1.00 | watch (n=12 < 20) |


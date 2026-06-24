# Engine learnings — realized edge by bucket

_Generated 2026-06-24T14:40:30.458152+00:00 · from the outcomes ledger. Buckets act on the scanner only at n ≥ 20 closes (shrunk toward the global prior). Below that they're shown but inert (×1.00)._

**Global: 34 closed · win rate 32% · realized $-4330.50**

## asset_class

| value | n | win rate | shrunk | avg P&L | total | ×mult | call |
|---|---:|---:|---:|---:|---:|---:|---|
| index_etf | 13 | 54% | 44% | $-4 | $-50 | ×1.00 | watch (n=13 < 20) |
| sector_etf | 1 | 0% | 29% | $-418 | $-418 | ×1.00 | watch (n=1 < 20) |
| single_name | 20 | 20% | 24% | $-193 | $-3862 | ×0.74 | AVOID (neg expectancy; wr 24% < prior 32%) |

## structure

| value | n | win rate | shrunk | avg P&L | total | ×mult | call |
|---|---:|---:|---:|---:|---:|---:|---|
| iron_condor | 6 | 0% | 20% | $-197 | $-1182 | ×1.00 | watch (n=6 < 20) |
| short_put_vertical | 22 | 46% | 41% | $-55 | $-1219 | ×1.28 | favor |
| short_call_vertical | 6 | 17% | 26% | $-322 | $-1930 | ×1.00 | watch (n=6 < 20) |

## cluster

| value | n | win rate | shrunk | avg P&L | total | ×mult | call |
|---|---:|---:|---:|---:|---:|---:|---|
| us_index | 6 | 100% | 58% | $+107 | $+642 | ×1.00 | watch (n=6 < 20) |
| consumer | 1 | 0% | 29% | $-385 | $-385 | ×1.00 | watch (n=1 < 20) |
| metals | 1 | 0% | 29% | $-418 | $-418 | ×1.00 | watch (n=1 < 20) |
| energy | 2 | 50% | 35% | $-247 | $-494 | ×1.00 | watch (n=2 < 20) |
| financials | 1 | 0% | 29% | $-850 | $-850 | ×1.00 | watch (n=1 < 20) |
| us_tech | 23 | 17% | 22% | $-123 | $-2825 | ×0.68 | AVOID (neg expectancy; wr 22% < prior 32%) |

## size

| value | n | win rate | shrunk | avg P&L | total | ×mult | call |
|---|---:|---:|---:|---:|---:|---:|---|
| 1x | 2 | 50% | 35% | $-76 | $-152 | ×1.00 | watch (n=2 < 20) |
| 3x | 5 | 40% | 35% | $-95 | $-476 | ×1.00 | watch (n=5 < 20) |
| 2x | 15 | 40% | 37% | $-57 | $-851 | ×1.00 | watch (n=15 < 20) |
| 4x | 12 | 17% | 24% | $-238 | $-2852 | ×1.00 | watch (n=12 < 20) |


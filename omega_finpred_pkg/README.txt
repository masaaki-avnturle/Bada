omega_finpred_pkg

This package provides simple tools to:
- ingest CSV price data (date,symbol,price)
- compute a complex transform zeta(x) = i*sin(i*x*log(x)) per price value
- save per-symbol transformed series under data/<symbol>.csv
- run simple prediction (moving average or linear regression) to produce a point forecast

See bin/finpred usage for details.

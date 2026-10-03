# Calculation contract — volatility attribution only

These are explicit conventions for the 12-feature MVP. Use decimal returns
internally and label horizons/units. This is historical portfolio-risk analysis,
not a forecast or a realized trading-strategy track record.

## 1. Portfolio and daily returns
The portfolio CSV supplies unique ticker labels and finite nonnegative weights
w summing to 1 within absolute tolerance 1e-8. Do not silently normalize weights.
Join weights and data by ticker before converting to arrays; column order must
not change any calculation. Zero weights are allowed; total zero is invalid.

P[t,i] denotes positive adjusted closing prices in the same currency (USD).
Daily simple return r[t,i] = P[t,i] / P[t-1,i] - 1.
No implicit forward filling, interpolation, or zero substitution. Compute returns
on the sorted union date index first, requiring both adjacent prices, then keep
rows with finite returns for every requested ticker. Dropping incomplete prices
before computing returns can accidentally turn multi-day changes into daily ones.
Reject duplicate dates and nonpositive/nonfinite observed prices. Missing prices
are diagnosed separately, not treated as observed zero or infinite prices.

Use the latest 756 complete return rows, requiring >=252 for the dashboard;
small unit tests need not meet the UI's minimum. Show actual dates and sample size.
A trading day missing from all series cannot be detected without an exchange
calendar: disclose that limitation instead of adding calendar infrastructure.

Portfolio return r_p[t] = sum_i w[i] * r[t,i]. This fixed-weight historical
series assumes daily rebalancing without costs/taxes. It is not a buy-and-hold
return series. Use this same aligned sample for all static metrics.

## 2. Asset volatility and matrices
Daily asset volatility sigma_i = sample_std(r[:,i], ddof=1).
Annualized asset volatility = sqrt(252) * sigma_i.
Daily covariance S = sample covariance of aligned daily returns, ddof=1.
Show S as daily return covariance (decimal return squared). Correlation is
Pearson correlation on the same complete sample; it is dimensionless.
Constant series have undefined correlations: show those cells unavailable,
including their diagonal. Do not substitute 0 or 1 without justification.

## 3. Portfolio volatility and rolling volatility
Daily variance v = w.T @ S @ w.
Daily portfolio volatility sigma_p = sqrt(v).
Annualized portfolio volatility sigma_ann = sqrt(252) * sigma_p.
Check that std(r_p, ddof=1) equals sigma_p for the same sample.
Annualization is a convention, not a guarantee about future annual risk.

Rolling volatility uses 60 consecutive rows of daily portfolio returns, ddof=1,
multiplied by sqrt(252). First 59 observations are unavailable, not zero.
Retain a mask of excluded return dates. If a 60-row window spans an explicitly
excluded return date, show that window unavailable; do not compact away the gap
and call the result 60 consecutive trading observations. Plot gaps without joining
them. The whole-market missing-day limitation above still applies.

## 4. Marginal, component and percentage risk
For sigma_p > 1e-12:
- Daily marginal risk MRC[i] = (S @ w)[i] / sigma_p.
- Daily component risk CRC[i] = w[i] * MRC[i].
- Fractional risk contribution share[i] = CRC[i] / sigma_p.
- Percentage contribution = 100 * share[i] in the displayed table/chart.
- Annualized MRC and CRC equal the daily values multiplied by sqrt(252).

Invariants: sum(CRC) = sigma_p; sum(annualized CRC) = sigma_ann;
sum(shares) = 1; sum(displayed percentages) = 100 before rounding.
Annualized CRC 0.025 contributes 2.5 volatility percentage points. A risk share
of 0.25 means 25% of total volatility: never confuse those two quantities.
MRC is the unconstrained sensitivity to an extra unit of weight, not a percentage
share. For a fully invested reallocation from j to i, the local sensitivity is
MRC[i] - MRC[j], because weights must still sum to one.

Negative contributions are valid: preserve them and use signed bars. Long-only
weights do not imply every risk contribution is positive. No covariance inverse
is needed; a singular covariance matrix is acceptable.
For sigma_p <= 1e-12, show zero/negligible volatility and mark attribution and
risk shares unavailable with an explanation, rather than dividing by zero.
Reject materially negative variance or invalid covariance inputs. If v is a tiny
negative numerical artifact (absolute value <=1e-14 in daily squared-return units),
clamp to zero and retain a diagnostic; do not hide larger inconsistencies.

## 5. Diversification benefit
Weighted standalone daily volatility B = sum_i w[i] * sigma_i.
Define diversification benefit = 1 - sigma_p / B for B > 1e-12.
Show as a percentage reduction relative to weighted standalone volatility.
This is the chosen definition; it is not expected-return improvement or a loss
probability. Compute numerator and denominator at the same daily/annual horizon.
If B <=1e-12, mark the benefit unavailable. If B>1e-12 and sigma_p=0, benefit is
100%, even though risk shares are undefined. Do not add a second ratio metric.

## 6. Independent examples and tests
Float tolerance: typically rtol=1e-8 and atol=1e-10 for normal-scale examples.

| Example | Expected |
|---|---|
| Daily asset std 0.02 | Annualized std 0.02*sqrt(252), approximately 0.3174901573 |
| S=diag(0.0004,0.0001), w=(0.5,0.5) | Daily variance 0.000125; volatility 0.0111803398875 |
| Same two-asset example | MRC=(0.01788854382,0.004472135955); CRC=(0.00894427191,0.0022360679775); shares=(0.8,0.2) |
| Same two-asset example | B=0.015; diversification benefit approximately 0.2546440075 |
| One asset with daily std 0.02, weight 1 | Vol 0.02, MRC/CRC 0.02, share 1, diversification benefit 0 |
| Perfectly correlated equal-volatility assets, weights totaling 1 | Portfolio std equals each asset std; diversification benefit 0; singular S allowed |
| S=[[0.0004,-0.00015],[-0.00015,0.0001]], w=(0.2,0.8) | Daily vol sqrt(0.000032); first component negative; sum identity preserved |
| tests/fixtures/prices_synthetic.csv | A returns=(0.1,-0.1,0); B=(0,0.1,0); equal-weight portfolio=(0.05,0,0) |

Also test: CSV missing/duplicate tickers; malformed/nonfinite weights; sum !=1;
one-asset matrix shape; zero-weight asset; reordered ticker labels; constant
series and zero-risk portfolio; duplicate dates; interior missing prices; missing
requested ticker; rolling window length/gaps; and unknown or unavailable data.
Use small independent known values; do not test finance solely against a duplicate
of the implementation formula. No test needs live market-provider access.

## Reference
[Euler risk contribution background](https://docs.mosek.com/portfolio-cookbook/risk_parity.html).
This project's numerical conventions and examples are specified above. No MOSEK
package or optimization engine is required.

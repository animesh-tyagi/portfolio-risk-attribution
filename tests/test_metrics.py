"""Offline M2 known answers; all constructed histories are synthetic test data."""

import math

import numpy as np
import pandas as pd
import pytest

from portfolio_risk import data, metrics


def returns_frame(values, columns=("A", "B")):
    return pd.DataFrame(values, columns=columns,
                        index=pd.date_range("2024-01-02", periods=len(values), freq="B"))


def prices_from_returns(returns):
    index = pd.date_range("2023-01-02", periods=len(returns) + 1, freq="B")
    values = np.vstack([np.ones(returns.shape[1]), np.cumprod(1 + returns.to_numpy(), axis=0)]) * 100
    return pd.DataFrame(values, columns=returns.columns, index=index)


@pytest.fixture
def prices():
    return data.load_price_csv("tests/fixtures/prices_synthetic.csv", ["A", "B"])


@pytest.fixture
def weights():
    return pd.Series({"B": 0.5, "A": 0.5}, name="weight")


def test_fixture_known_answers_and_reconciliation(prices, weights):
    result = metrics.calculate_metrics(prices.iloc[::-1], weights, min_observations=2)
    np.testing.assert_allclose(result.sample.returns, [[.1, 0], [-.1, .1], [0, 0]], atol=1e-15)
    np.testing.assert_allclose(result.asset_volatility, [.1 * math.sqrt(252), math.sqrt(.003333333333333333 * 252)])
    np.testing.assert_allclose(result.covariance, [[.01, -.005], [-.005, 1 / 300]])
    np.testing.assert_allclose(result.correlation, [[1, -math.sqrt(3) / 2], [-math.sqrt(3) / 2, 1]])
    np.testing.assert_allclose(result.portfolio_returns, [.05, 0, 0], atol=1e-15)
    assert result.portfolio_volatility.daily_variance == pytest.approx(1 / 1200)
    assert result.portfolio_volatility.daily == pytest.approx(.02886751345948129)
    assert result.portfolio_volatility.annualized == pytest.approx(math.sqrt(.21))
    assert result.portfolio_returns.std(ddof=1) == pytest.approx(result.portfolio_volatility.daily)
    assert result.rolling_volatility.isna().all()  # <60 returns, never padded
    assert result.sample.diagnostics["selected_return_rows"] == 3
    assert result.sample.diagnostics["excluded_return_rows"] == 0
    assert result.sample.diagnostics["sample_first_date"] == prices.index[1].date().isoformat()


def test_independent_diagonal_covariance_example(weights):
    covariance = pd.DataFrame([[.0004, 0], [0, .0001]], index=["A", "B"], columns=["A", "B"])
    answer = metrics.portfolio_volatility(covariance, weights)
    assert answer.daily_variance == pytest.approx(.000125)
    assert answer.daily == pytest.approx(.011180339887498949)
    assert answer.annualized == pytest.approx(.17748239349298847)
    assert answer.diagnostics == ()


def test_std_annualization_covariance_ddof_and_zero_correlation(weights):
    r = returns_frame([[-.02, .01 / math.sqrt(3)], [0, -.02 / math.sqrt(3)], [.02, .01 / math.sqrt(3)]])
    np.testing.assert_allclose(metrics.annualized_asset_volatility(r), [.3174901573277509, .15874507866387544])
    np.testing.assert_allclose(metrics.daily_covariance(r), [[.0004, 0], [0, .0001]], atol=1e-18)
    np.testing.assert_allclose(metrics.correlation_matrix(r), np.eye(2), atol=1e-15)
    answer = metrics.portfolio_volatility(metrics.daily_covariance(r), weights)
    assert answer.daily == pytest.approx(metrics.portfolio_returns(r, weights).std(ddof=1))


def test_one_asset_matrix_shapes_and_reconciliation():
    r = returns_frame([[-.02], [0], [.02]], ("SOLO",))
    w = pd.Series({"SOLO": 1.0})
    cov, corr = metrics.daily_covariance(r), metrics.correlation_matrix(r)
    assert cov.shape == corr.shape == (1, 1)
    assert list(cov.index) == list(cov.columns) == ["SOLO"]
    assert cov.iloc[0, 0] == pytest.approx(.0004)
    assert corr.iloc[0, 0] == pytest.approx(1)
    assert metrics.portfolio_volatility(cov, w).daily == pytest.approx(.02)
    p = prices_from_returns(r)
    result = metrics.calculate_metrics(p, w, min_observations=2, rolling_window=2)
    assert result.covariance.shape == (1, 1)
    assert result.portfolio_volatility.daily == pytest.approx(result.portfolio_returns.std(ddof=1))


def test_constant_assets_correlations_unavailable_and_zero_volatility():
    r = returns_frame([[-.02, 0], [0, 0], [.02, 0]])
    corr = metrics.correlation_matrix(r)
    assert corr.loc["B"].isna().all() and corr["B"].isna().all()
    assert corr.loc["A", "A"] == pytest.approx(1)
    assert metrics.annualized_asset_volatility(r)["B"] == 0
    assert metrics.portfolio_volatility(metrics.daily_covariance(r), pd.Series({"A": 0., "B": 1.})).daily == 0
    result = metrics.calculate_metrics(prices_from_returns(r), pd.Series({"A": 0., "B": 1.}), min_observations=2)
    assert result.portfolio_volatility.annualized == 0
    assert any("constant-return assets: B" in warning for warning in result.warnings)
    constant = r * 0
    assert metrics.correlation_matrix(constant).isna().all().all()
    single = constant[["B"]]
    assert metrics.correlation_matrix(single).shape == (1, 1)
    assert math.isnan(metrics.correlation_matrix(single).iloc[0, 0])


def test_nonzero_constant_returns_have_undefined_correlations():
    r = returns_frame([[.01, -.02], [.01, -.02], [.01, -.02]])
    assert metrics.correlation_matrix(r).isna().all().all()
    np.testing.assert_allclose(metrics.daily_covariance(r), 0, atol=1e-30)


def test_singular_covariance_perfect_correlation_and_exact_hedge():
    r = returns_frame([[-.02, -.02], [0, 0], [.02, .02]])
    np.testing.assert_allclose(metrics.correlation_matrix(r), 1)
    w = pd.Series({"A": .2, "B": .8})
    assert metrics.portfolio_volatility(metrics.daily_covariance(r), w).daily == pytest.approx(.02)
    r["B"] = -r["A"]
    answer = metrics.portfolio_volatility(metrics.daily_covariance(r), pd.Series({"A": .5, "B": .5}))
    assert answer.daily == 0


def test_alignment_is_by_ticker_for_columns_covariance_rows_and_weights(prices):
    w = pd.Series({"A": .25, "B": .75})
    r = metrics.prepare_returns(prices).returns
    expected = metrics.portfolio_returns(r, w)
    pd.testing.assert_series_equal(metrics.portfolio_returns(r[["B", "A"]], w.iloc[::-1]), expected)
    cov = metrics.daily_covariance(r)
    expected_vol = metrics.portfolio_volatility(cov, w)
    assert metrics.portfolio_volatility(cov.loc[["B", "A"], ["A", "B"]], w.iloc[::-1]) == expected_vol
    result = metrics.calculate_metrics(prices[["B", "A"]], w, min_observations=2)
    pd.testing.assert_series_equal(result.portfolio_returns, expected)


def test_missing_prices_exclude_two_returns_without_bridging(prices):
    prices.loc[prices.index[1], "A"] = np.nan
    daily = metrics.daily_returns(prices.iloc[::-1])
    assert daily.iloc[:2]["A"].isna().all()
    assert daily.iloc[2]["A"] == 0
    np.testing.assert_allclose(daily["B"], [0, .1, 0], atol=1e-15)
    with pytest.raises(metrics.MetricsError, match="1 usable"):
        metrics.prepare_returns(prices)


def test_common_sample_lookback_counts_dates_and_trailing_gap():
    r = returns_frame(np.tile([[-.01, .02], [.01, -.02]], (5, 1)))
    p = prices_from_returns(r)
    p.loc[p.index[4], "B"] = np.nan
    p.loc[p.index[-1], "A"] = np.nan
    sample = metrics.prepare_returns(p, lookback_returns=4)
    assert sample.excluded_dates.loc[p.index[[4, 5, 10]]].all()
    assert sample.diagnostics["complete_return_rows"] == 7
    assert sample.diagnostics["selected_return_rows"] == 4
    assert sample.diagnostics["complete_rows_outside_lookback"] == 3
    assert sample.diagnostics["missing_prices_by_ticker"] == {"A": 1, "B": 1}
    assert sample.diagnostics["unavailable_returns_by_ticker"] == {"A": 1, "B": 2}
    assert list(sample.returns.index) == list(p.index[6:10])
    result = metrics.calculate_metrics(p, pd.Series({"A": .5, "B": .5}), lookback_returns=4,
                                       min_observations=2, rolling_window=2)
    assert result.rolling_volatility.index[-1] == p.index[-1]
    assert math.isnan(result.rolling_volatility.iloc[-1])
    assert any("Excluded 3" in warning for warning in result.warnings)


def test_dashboard_minimum_and_latest_756_selection():
    r = returns_frame(np.tile([[-.01], [.01]], (400, 1)), ("A",))
    p = prices_from_returns(r)
    result = metrics.calculate_metrics(p, pd.Series({"A": 1.}))
    assert len(result.sample.returns) == 756
    assert result.sample.returns.index[0] == p.index[-756]
    assert len(result.rolling_volatility) == 756
    assert result.rolling_volatility.iloc[:59].isna().all()
    assert result.rolling_volatility.iloc[59:].notna().all()
    with pytest.raises(metrics.MetricsError, match="require 252"):
        metrics.calculate_metrics(p.iloc[:252], pd.Series({"A": 1.}))
    assert len(metrics.calculate_metrics(p.iloc[:253], pd.Series({"A": 1.})).sample.returns) == 252


def test_sixty_row_rolling_known_answer():
    r = returns_frame([[.01 if i % 2 else -.01] for i in range(65)], ("A",))
    answer = metrics.rolling_portfolio_volatility(r, pd.Series({"A": 1.}))
    assert len(answer) == 65
    assert answer.iloc[:59].isna().all()
    # 30 of each +/-1%: mean 0, squared-deviation sum .006, divide by 59.
    np.testing.assert_allclose(answer.iloc[59:], math.sqrt(.006 / 59 * 252))
    assert metrics.rolling_portfolio_volatility(r.iloc[:59], pd.Series({"A": 1.})).isna().all()
    assert metrics.rolling_portfolio_volatility(r * 0, pd.Series({"A": 1.})).iloc[59:].eq(0).all()


def test_rolling_gap_blocks_full_windows_and_recovers_after_sixty_rows():
    r = returns_frame([[.01 if i % 2 else -.01, 0] for i in range(140)])
    p = prices_from_returns(r)
    p.loc[p.index[65], "B"] = np.nan
    sample = metrics.prepare_returns(p)
    w = pd.Series({"A": 1., "B": 0.})  # zero weight must not bypass common-sample rules
    answer = metrics.rolling_portfolio_volatility(sample.daily_returns, w)
    assert answer.loc[p.index[60:65]].notna().all()
    assert answer.loc[p.index[65:126]].isna().all()  # missing return dates 65 and 66
    assert answer.loc[p.index[126:]].notna().all()
    assert len(answer) == 140  # dates are retained, not compacted
    result = metrics.calculate_metrics(p, w, min_observations=2)
    pd.testing.assert_series_equal(result.rolling_volatility, answer)
    assert result.portfolio_volatility.daily == pytest.approx(result.portfolio_returns.std(ddof=1))


@pytest.mark.parametrize("bad", [np.nan, np.inf, -np.inf])
def test_static_metrics_reject_incomplete_or_nonfinite_returns(bad):
    r = returns_frame([[.01, 0], [bad, .02], [-.01, -.02]])
    for fn in (metrics.annualized_asset_volatility, metrics.daily_covariance, metrics.correlation_matrix):
        with pytest.raises(metrics.MetricsError, match="complete finite"):
            fn(r)


def test_nonfinite_ratio_diagnosed_without_inventing_return():
    p = pd.DataFrame({"A": [1e-300, 1e300, 1e300, 1e300]}, index=pd.date_range("2024-01-01", periods=4))
    sample = metrics.prepare_returns(p)
    assert sample.excluded_dates.iloc[0]
    assert sample.diagnostics["unavailable_returns_by_ticker"] == {"A": 1}
    assert sample.returns["A"].eq(0).all()


@pytest.mark.parametrize("w", [pd.Series({"A": .2, "B": .2}), pd.Series({"A": -.1, "B": 1.1}),
    pd.Series({"A": np.nan, "B": 1.}), pd.Series({"A": np.inf, "B": 0.}),
    pd.Series({"A": 1.}), pd.Series([.5, .5], index=["A", "A"]), [.5, .5]])
def test_invalid_weights(w):
    r = returns_frame([[-.01, 0], [0, .01], [.01, 0]])
    with pytest.raises(metrics.MetricsError):
        metrics.portfolio_returns(r, w)
    with pytest.raises(metrics.MetricsError):
        metrics.portfolio_volatility(metrics.daily_covariance(r), w)


@pytest.mark.parametrize("matrix", [ [[.0004, .0001], [0, .0001]], [[.0004, np.nan], [np.nan, .0001]],
    [[.0004, .0003], [.0003, .0001]], [[-.0004, 0], [0, .0001]] ])
def test_invalid_covariance_including_indefinite_with_positive_weighted_variance(matrix, weights):
    cov = pd.DataFrame(matrix, index=["A", "B"], columns=["A", "B"])
    with pytest.raises(metrics.MetricsError):
        metrics.portfolio_volatility(cov, weights)


def test_tiny_negative_variance_clamps_with_diagnostic():
    cov = pd.DataFrame([[-5e-15]], index=["A"], columns=["A"])
    answer = metrics.portfolio_volatility(cov, pd.Series({"A": 1.}))
    assert answer.daily_variance == answer.daily == answer.annualized == 0
    assert "clamped" in answer.diagnostics[0]


def test_invalid_covariance_labels(weights):
    cov = pd.DataFrame(np.eye(2), index=["A", "C"], columns=["A", "B"])
    with pytest.raises(metrics.MetricsError, match="tickers must match"):
        metrics.portfolio_volatility(cov, weights)


@pytest.mark.parametrize("change", ["duplicate-date", "unsorted", "invalid-date", "duplicate-ticker", "nonnumeric", "single-row"])
def test_invalid_return_inputs(change):
    r = returns_frame([[.01, 0], [0, .01], [-.01, 0]])
    if change == "duplicate-date":
        r.index = pd.DatetimeIndex([r.index[0], r.index[0], r.index[2]])
    elif change == "unsorted":
        r = r.iloc[::-1]
    elif change == "invalid-date":
        r.index = pd.RangeIndex(3)
    elif change == "duplicate-ticker":
        r.columns = ["A", "A"]
    elif change == "nonnumeric":
        r = r.astype(object)
        r.iloc[0, 0] = "bad"
    else:
        r = r.iloc[:1]
    with pytest.raises(metrics.MetricsError):
        metrics.daily_covariance(r)


@pytest.mark.parametrize("kwargs", [{"lookback_returns": 1}, {"min_observations": 1},
    {"lookback_returns": 2, "min_observations": 3}, {"lookback_returns": True}])
def test_invalid_sample_settings(prices, kwargs):
    with pytest.raises(metrics.MetricsError):
        metrics.prepare_returns(prices, **kwargs)


def test_invalid_rolling_and_annualization_parameters():
    r = returns_frame([[-.01], [.01]], ("A",))
    with pytest.raises(metrics.MetricsError):
        metrics.rolling_portfolio_volatility(r, pd.Series({"A": 1.}), window=1)
    with pytest.raises(metrics.MetricsError):
        metrics.annualized_asset_volatility(r, trading_days=0)


def test_price_validation_reused_before_return_arithmetic(prices):
    for p in (pd.concat([prices, prices.iloc[:1]]), prices.assign(A=-1)):
        with pytest.raises(data.DataError):
            metrics.daily_returns(p)
    assert metrics.daily_returns(prices.iloc[:1]).empty
    with pytest.raises(metrics.MetricsError, match="Insufficient"):
        metrics.prepare_returns(prices.iloc[:1])

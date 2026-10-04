"""Offline M3 independent numerical answers and Euler identities."""

import math

import numpy as np
import pandas as pd
import pytest

from portfolio_risk import attribution, data, metrics


def covariance(values, labels=("A", "B")):
    return pd.DataFrame(values, index=labels, columns=labels)


def test_documented_two_asset_known_answers():
    result = attribution.calculate_attribution(
        covariance([[.0004, 0], [0, .0001]]), pd.Series({"A": .5, "B": .5}))
    t = result.table
    np.testing.assert_allclose(t.daily_asset_volatility, [.02, .01])
    np.testing.assert_allclose(t.daily_marginal_contribution, [.01788854382, .004472135955])
    np.testing.assert_allclose(t.daily_component_contribution, [.00894427191, .0022360679775])
    np.testing.assert_allclose(t.risk_share, [.8, .2])
    assert result.portfolio_volatility.daily == pytest.approx(.011180339887498949)
    assert result.weighted_standalone_daily_volatility == pytest.approx(.015)
    assert result.diversification_benefit == pytest.approx(.2546440075000701)
    assert result.attribution_unavailable_reason is None
    assert result.diversification_unavailable_reason is None
    assert result.diagnostics == ()


@pytest.mark.parametrize("matrix, weights", [
    ([[.0004, 0], [0, .0001]], [.5, .5]),
    ([[.0004, -.00015], [-.00015, .0001]], [.2, .8]),
    ([[.0004, .0004], [.0004, .0004]], [.2, .8]),
    ([[.0004, .0001], [.0001, .0001]], [1., 0.]),
])
def test_component_and_share_identities_and_annualization(matrix, weights):
    result = attribution.calculate_attribution(covariance(matrix), pd.Series(weights, index=["A", "B"]))
    t, vol = result.table, result.portfolio_volatility
    assert t.daily_component_contribution.sum() == pytest.approx(vol.daily, rel=1e-8, abs=1e-10)
    assert t.annualized_component_contribution.sum() == pytest.approx(vol.annualized)
    assert t.risk_share.sum() == pytest.approx(1.)
    assert (100 * t.risk_share).sum() == pytest.approx(100.)
    for measure in ("asset_volatility", "marginal_contribution", "component_contribution"):
        np.testing.assert_allclose(t["annualized_" + measure], t["daily_" + measure] * math.sqrt(252))


def test_negative_component_known_answer_preserved():
    result = attribution.calculate_attribution(covariance([[.0004, -.00015], [-.00015, .0001]]),
                                               pd.Series({"A": .2, "B": .8}))
    # S w=(-.00004,.00005), daily vol=sqrt(.000032).
    np.testing.assert_allclose(result.table.daily_component_contribution,
                               [-.001414213562373095, .007071067811865475])
    np.testing.assert_allclose(result.table.risk_share, [-.25, 1.25])
    assert result.diversification_benefit == pytest.approx(.5285954792089683)


def test_zero_weight_has_zero_component_but_nonzero_marginal():
    result = attribution.calculate_attribution(covariance([[.0004, .0001], [.0001, .0001]]),
                                               pd.Series({"A": 1., "B": 0.}))
    assert result.table.loc["B", "daily_marginal_contribution"] == pytest.approx(.005)
    assert result.table.loc["B", "daily_component_contribution"] == 0
    assert result.table.loc["B", "risk_share"] == 0
    assert result.diversification_benefit == pytest.approx(0.)


def test_single_asset_and_custom_annualization():
    result = attribution.calculate_attribution(covariance([[.0004]], ("SOLO",)),
                                               pd.Series({"SOLO": 1.}), trading_days=100)
    np.testing.assert_allclose(result.table.iloc[0], [1., .02, .2, .02, .2, .02, .2, 1.])
    assert result.diversification_benefit == pytest.approx(0.)


def test_singular_perfect_correlation():
    result = attribution.calculate_attribution(covariance([[.0004, .0004], [.0004, .0004]]),
                                               pd.Series({"A": .2, "B": .8}))
    np.testing.assert_allclose(result.table.daily_marginal_contribution, [.02, .02])
    np.testing.assert_allclose(result.table.risk_share, [.2, .8])
    assert result.diversification_benefit == pytest.approx(0.)


@pytest.mark.parametrize("matrix, weights, benefit", [
    ([[0, 0], [0, 0]], [.5, .5], np.nan),
    ([[.0004, -.0004], [-.0004, .0004]], [.5, .5], 1.),
    ([[.0004, 0], [0, 0]], [0., 1.], np.nan),
    ([[1e-26, 0], [0, 1e-26]], [.5, .5], np.nan),
])
def test_zero_or_negligible_risk_unavailable_with_reason(matrix, weights, benefit):
    result = attribution.calculate_attribution(covariance(matrix), pd.Series(weights, index=["A", "B"]))
    assert result.portfolio_volatility.daily <= 1e-12
    assert result.table.filter(regex="contribution|risk_share").isna().all().all()
    assert "zero/negligible" in result.attribution_unavailable_reason
    if math.isnan(benefit):
        assert math.isnan(result.diversification_benefit)
        assert "standalone" in result.diversification_unavailable_reason
    else:
        assert result.diversification_benefit == benefit
        assert result.diversification_unavailable_reason is None


def test_negligible_portfolio_with_positive_standalone_still_computes_benefit():
    result = attribution.calculate_attribution(covariance([[4e-24, -4e-24], [-4e-24, 4e-24]]),
                                               pd.Series({"A": .6, "B": .4}))
    assert result.attribution_unavailable_reason is not None
    assert result.weighted_standalone_daily_volatility == pytest.approx(2e-12, abs=1e-25)
    assert result.diversification_unavailable_reason is None
    assert result.diversification_benefit == pytest.approx(.8)


def test_exact_negligible_threshold_is_unavailable():
    result = attribution.calculate_attribution(covariance([[1e-24]], ("A",)), pd.Series({"A": 1.}))
    assert result.portfolio_volatility.daily == 1e-12
    assert result.attribution_unavailable_reason is not None
    assert result.diversification_unavailable_reason is not None


def test_rounding_scale_negative_variance_retains_diagnostic():
    result = attribution.calculate_attribution(covariance([[-5e-15]], ("A",)), pd.Series({"A": 1.}))
    assert result.portfolio_volatility.daily == 0
    assert result.table.daily_asset_volatility.isna().all()
    assert math.isnan(result.diversification_benefit)
    assert "negative covariance diagonal" in result.diversification_unavailable_reason
    assert any("clamped" in d for d in result.diagnostics)


def test_reordered_covariance_axes_and_weights_preserve_ticker_answers():
    cov = covariance([[.0004, -.00015], [-.00015, .0001]])
    w = pd.Series({"A": .2, "B": .8})
    expected = attribution.calculate_attribution(cov, w)
    result = attribution.calculate_attribution(cov.loc[["B", "A"], ["A", "B"]], w.iloc[::-1])
    pd.testing.assert_frame_equal(result.table.loc[w.index], expected.table)
    assert list(result.table.index) == ["B", "A"]
    assert result.diversification_benefit == pytest.approx(expected.diversification_benefit)
    assert result.portfolio_volatility.daily == pytest.approx(expected.portfolio_volatility.daily)


def test_m2_synthetic_price_pipeline_and_reordered_columns():
    prices = data.load_price_csv("tests/fixtures/prices_synthetic.csv", ["A", "B"])
    w = pd.Series({"A": .5, "B": .5})
    answers = []
    for p in (prices, prices[["B", "A"]]):
        m = metrics.calculate_metrics(p, w, min_observations=2)
        a = attribution.calculate_attribution(m.covariance, w)
        assert a.portfolio_volatility == m.portfolio_volatility
        np.testing.assert_allclose(a.table.risk_share, [1.5, -.5], atol=1e-10)
        answers.append(a)
    pd.testing.assert_frame_equal(answers[0].table, answers[1].table)


@pytest.mark.parametrize("matrix", [
    [[.0004, .0001], [0, .0001]], [[.0004, np.nan], [np.nan, .0001]],
    [[.0004, np.inf], [np.inf, .0001]], [[.0004, .0003], [.0003, .0001]],
    [[-.0004, 0], [0, .0001]], [["bad", 0], [0, .0001]],
])
def test_invalid_covariance(matrix):
    with pytest.raises(metrics.MetricsError):
        attribution.calculate_attribution(covariance(matrix), pd.Series({"A": .5, "B": .5}))


@pytest.mark.parametrize("weights", [pd.Series({"A": .2, "B": .2}),
    pd.Series({"A": -.1, "B": 1.1}), pd.Series({"A": np.nan, "B": 1.}),
    pd.Series({"A": np.inf, "B": 0.}), pd.Series({"A": 1.}),
    pd.Series([.5, .5], index=["A", "A"]), [.5, .5]])
def test_invalid_weights(weights):
    with pytest.raises(metrics.MetricsError):
        attribution.calculate_attribution(covariance([[.0004, 0], [0, .0001]]), weights)


def test_invalid_labels_and_annualization():
    cov = covariance([[.0004, 0], [0, .0001]])
    w = pd.Series({"A": .5, "B": .5})
    for bad in (cov.rename(index={"B": "C"}), cov.set_axis(["A", "A"]), cov.to_numpy()):
        with pytest.raises(metrics.MetricsError):
            attribution.calculate_attribution(bad, w)
    with pytest.raises(metrics.MetricsError):
        attribution.calculate_attribution(cov, w, trading_days=0)
